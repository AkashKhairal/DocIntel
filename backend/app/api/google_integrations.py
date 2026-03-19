from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_tenant_context
from app.core.config import get_settings
from app.db.session import get_db
from app.integrations import google as google_integration
from app.models.google_integration import GoogleIntegration
from workers.tasks import process_file_task

class MonitoredFoldersUpdate(BaseModel):
    folder_ids: List[str]

router = APIRouter(prefix="/integrations/google", tags=["google_integrations"])


@router.get("/connect")
async def connect_google_drive(current_user=Depends(get_current_user)):
    state = f"{current_user.tenant_id}:{current_user.id}"
    url, flow_state = google_integration.get_authorize_url(state=state)
    return {"url": url, "state": flow_state}


@router.get("/callback")
async def google_oauth_callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        if not code:
            frontend_url = get_settings().frontend_url.rstrip("/")
            return RedirectResponse(url=f"{frontend_url}/googledrive-callback?status=error&message=missing_code", status_code=302)

        # Parse tenant/user from state payload set in /connect
        tenant_id = None
        user_id = None
        if state and ":" in state:
            parts = state.split(":")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                tenant_id = int(parts[0])
                user_id = int(parts[1])

        try:
            token_data = google_integration.exchange_code(code)
        except Exception:
            frontend_url = get_settings().frontend_url.rstrip("/")
            return RedirectResponse(url=f"{frontend_url}/googledrive-callback?status=error&message=exchange_failed", status_code=302)

        # Fallback to default tenant if no state was provided (use first tenant)
        if tenant_id is None:
            session_data = await db.execute(text("SELECT * FROM tenants LIMIT 1"))
            tenant_row = session_data.first()
            tenant_id = tenant_row.id if tenant_row else 0

        existing = await db.execute(
            text("SELECT * FROM google_integrations WHERE tenant_id = :tenant_id AND user_id = :user_id"),
            {"tenant_id": tenant_id, "user_id": user_id},
        )
        integration_row = existing.mappings().first()

        if integration_row:
            integration = await db.get(GoogleIntegration, integration_row["id"])
            integration.access_token = token_data["access_token"]
            integration.refresh_token = token_data["refresh_token"]
            integration.expiry = token_data["expiry"]
            integration.scope = token_data.get("scope", "")
        else:
            integration = GoogleIntegration(
                tenant_id=tenant_id,
                user_id=user_id,
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expiry=token_data["expiry"],
                scope=token_data.get("scope", ""),
            )
            db.add(integration)

        await db.commit()
        await db.refresh(integration)

        # Register watch channel
        drive_service, creds, refreshed = google_integration.build_drive_service(
            integration.access_token,
            integration.refresh_token,
            integration.expiry,
        )

        start_token_response = drive_service.changes().getStartPageToken().execute()
        start_page_token = start_token_response.get("startPageToken")

        settings = get_settings()
        webhook_host = settings.webhook_url
        if not webhook_host:
            webhook_host = str(request.base_url).rstrip("/")

        watch_body = {
            "id": f"drive-webhook-{integration.id}",
            "type": "web_hook",
            "address": webhook_host.rstrip("/") + "/webhooks/google-drive",
        }

        try:
            result = drive_service.changes().watch(
                pageToken=start_page_token, body=watch_body).execute()
            integration.webhook_channel_id = result.get("id")
            integration.page_token = start_page_token
        except Exception as e:
            # Webhook registration might fail on localhost (no HTTPS)
            import logging
            logging.warning(f"Failed to register Google Drive webhook (likely due to no HTTPS on localhost): {e}")

        if refreshed:
            integration.access_token = creds.token
            integration.refresh_token = creds.refresh_token or integration.refresh_token
            integration.expiry = creds.expiry

        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        frontend_url = get_settings().frontend_url.rstrip("/")
        redirect_url = f"{frontend_url}/googledrive-callback?status=connected"
        return RedirectResponse(url=redirect_url, status_code=302)

    except Exception:
        import logging
        logging.exception("Google OAuth callback failed")
        frontend_url = get_settings().frontend_url.rstrip("/")
        return RedirectResponse(url=f"{frontend_url}/googledrive-callback?status=error&message=server_error", status_code=302)


@router.get("/status")
async def google_integration_status(tenant_context=Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT id, tenant_id, user_id, webhook_channel_id, expiry, scope, monitored_folders FROM google_integrations WHERE tenant_id = :tenant_id"),
        {"tenant_id": tenant_context["tenant_id"]},
    )
    integration = result.mappings().first()
    if not integration:
        raise HTTPException(
            status_code=404, detail="No Google Drive integration connected")
    return integration


@router.get("/")
async def get_integration(tenant_context=Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM google_integrations WHERE tenant_id = :tenant_id"), {"tenant_id": tenant_context["tenant_id"]})
    integration = result.mappings().first()
    if not integration:
        raise HTTPException(
            status_code=404, detail="No Google Drive integration connected")
    return integration


@router.get("/folders")
async def list_google_folders(
    parent_id: Optional[str] = "root",
    tenant_context=Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """List folders in Google Drive for a specific parent."""
    result = await db.execute(
        text("SELECT * FROM google_integrations WHERE tenant_id = :tenant_id"),
        {"tenant_id": tenant_context["tenant_id"]},
    )
    integration = result.mappings().first()
    if not integration:
        raise HTTPException(status_code=404, detail="No Google Drive integration connected")

    drive_service, _, _ = google_integration.build_drive_service(
        integration["access_token"],
        integration["refresh_token"],
        integration["expiry"],
    )

    query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    response = drive_service.files().list(
        q=query,
        fields="nextPageToken, files(id, name)",
        pageSize=100
    ).execute()

    return {"folders": response.get("files", []), "selected_folders": integration.get("monitored_folders") or []}


@router.patch("/monitored-folders")
async def update_monitored_folders(
    update: MonitoredFoldersUpdate,
    tenant_context=Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """Update the list of folder IDs to be monitored for changes."""
    result = await db.execute(
        text("SELECT * FROM google_integrations WHERE tenant_id = :tenant_id"),
        {"tenant_id": tenant_context["tenant_id"]},
    )
    integration_row = result.mappings().first()
    if not integration_row:
        raise HTTPException(status_code=404, detail="No Google Drive integration connected")

    integration = await db.get(GoogleIntegration, integration_row["id"])
    integration.monitored_folders = update.folder_ids
    db.add(integration)
    await db.commit()
    await db.refresh(integration)

    return {"status": "success", "monitored_folders": integration.monitored_folders}


@router.post("/webhooks/google-drive")
async def google_drive_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    channel_id = request.headers.get("X-Goog-Channel-ID")
    resource_state = request.headers.get("X-Goog-Resource-State")

    if not channel_id or not resource_state:
        raise HTTPException(status_code=400, detail="Missing webhook headers")

    result = await db.execute(text("SELECT * FROM google_integrations WHERE webhook_channel_id = :channel_id"), {"channel_id": channel_id})
    integration = result.mappings().first()
    if not integration:
        raise HTTPException(
            status_code=404, detail="Integration channel not found")

    # fetch changes from Drive
    drive_service, creds, refreshed = google_integration.build_drive_service(
        integration["access_token"], integration["refresh_token"], integration["expiry"]
    )

    if refreshed:
        integration_obj = await db.get(GoogleIntegration, integration["id"])
        integration_obj.access_token = creds.token
        integration_obj.refresh_token = creds.refresh_token or integration_obj.refresh_token
        integration_obj.expiry = creds.expiry
        db.add(integration_obj)
        await db.commit()

    page_token = integration.get("page_token")
    if not page_token:
        start = drive_service.changes().getStartPageToken().execute()
        page_token = start.get("startPageToken")

    changes = []
    next_page_token = page_token

    while next_page_token:
        response = drive_service.changes().list(
            pageToken=next_page_token,
            fields="nextPageToken,newStartPageToken,changes(fileId,file(name,mimeType,trashed,createdTime,modifiedTime,webViewLink,parents),removed)",
            includeRemoved=True,
        ).execute()

        changes.extend(response.get("changes", []))
        next_page_token = response.get("nextPageToken")

        # update the page token each page
        integration_row = await db.get(GoogleIntegration, integration["id"])
        integration_row.page_token = response.get(
            "newStartPageToken") or next_page_token
        db.add(integration_row)
        await db.commit()

    # enqueue indexing tasks
    for change in changes:
        file_id = change.get("fileId")
        removed = change.get("removed", False)
        file_info = change.get("file", {})
        trashed = file_info.get("trashed", False)

        if not file_id:
            continue

        if removed or trashed:
            from workers.tasks import delete_file_vectors_task
            delete_file_vectors_task.delay(file_id)
        else:
            process_file_task.delay(
                file_id,
                tenant_id=integration["tenant_id"],
                organization_id=integration["tenant_id"],
                user_id=integration.get("user_id"),
                access_token=integration["access_token"],
                refresh_token=integration["refresh_token"],
                expiry=integration["expiry"],
            )

    return {"status": "received", "changes": len(changes)}

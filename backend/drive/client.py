"""Google Drive API v3 client for file operations and watch channels."""

import json
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from config.settings import get_settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _get_drive_service():
    """Build and return a Google Drive API service instance."""
    settings = get_settings()
    if not settings.google_credentials_json:
        raise ValueError("Google credentials not configured. Please set them via Settings.")

    creds_dict = json.loads(settings.google_credentials_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials)


def download_file(file_id: str) -> tuple[Path, dict]:
    """Download a file from Google Drive to a temp location.

    Returns:
        Tuple of (local_path, file_metadata)
    """
    service = _get_drive_service()

    # Get file metadata
    file_meta = (
        service.files()
        .get(fileId=file_id, fields="id,name,mimeType,createdTime,modifiedTime,webViewLink,parents")
        .execute()
    )

    mime = file_meta.get("mimeType", "")
    name = file_meta.get("name", "unknown")

    # Map Google Workspace types to export formats
    export_map = {
        "application/vnd.google-apps.document": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".docx",
        ),
        "application/vnd.google-apps.spreadsheet": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
        ),
        "application/vnd.google-apps.presentation": (
            "application/pdf",
            ".pdf",
        ),
    }

    suffix = Path(name).suffix or ".bin"

    if mime in export_map:
        export_mime, suffix = export_map[mime]
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
    else:
        request = service.files().get_media(fileId=file_id)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    import io

    fh = io.FileIO(tmp.name, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()

    return Path(tmp.name), file_meta


def get_folder_path(service, file_meta: dict) -> str:
    """Resolve the folder path for a file."""
    parents = file_meta.get("parents", [])
    if not parents:
        return "/"

    path_parts = []
    current_id = parents[0]
    while current_id:
        try:
            folder = service.files().get(fileId=current_id, fields="id,name,parents").execute()
            path_parts.insert(0, folder.get("name", ""))
            parents = folder.get("parents", [])
            current_id = parents[0] if parents else None
        except Exception:
            break
    return "/" + "/".join(path_parts) if path_parts else "/"


def list_all_files(folder_id: Optional[str] = None) -> list[dict]:
    """List all files in the configured Drive folder."""
    service = _get_drive_service()
    settings = get_settings()
    target_folder = folder_id or settings.google_drive_folder_id

    query = f"'{target_folder}' in parents and trashed = false" if target_folder else "trashed = false"

    results = []
    page_token = None
    while True:
        response = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id,name,mimeType,createdTime,modifiedTime,webViewLink,parents)",
                pageSize=100,
                pageToken=page_token,
            )
            .execute()
        )
        results.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return results


def setup_watch_channel() -> dict:
    """Create a Drive push notification watch channel."""
    service = _get_drive_service()
    settings = get_settings()

    if not settings.webhook_url:
        raise ValueError("Webhook URL not configured. Please set it via Settings.")

    # Get the start page token
    response = service.changes().getStartPageToken().execute()
    start_page_token = response.get("startPageToken")

    channel_id = str(uuid.uuid4())
    body = {
        "id": channel_id,
        "type": "web_hook",
        "address": settings.webhook_url.rstrip("/") + "/drive/webhook",
    }

    result = service.changes().watch(pageToken=start_page_token, body=body).execute()
    logger.info(f"Watch channel created: {channel_id}, expiration: {result.get('expiration')}")

    return {
        "channel_id": channel_id,
        "resource_id": result.get("resourceId"),
        "expiration": result.get("expiration"),
        "start_page_token": start_page_token,
    }


def get_changes(start_page_token: str) -> tuple[list[dict], str]:
    """Fetch changes since the given page token.

    Returns:
        Tuple of (list of changes, new page token)
    """
    service = _get_drive_service()

    changes = []
    page_token = start_page_token
    while page_token:
        response = (
            service.changes()
            .list(
                pageToken=page_token,
                fields="nextPageToken, newStartPageToken, changes(fileId,file(id,name,mimeType,trashed,createdTime,modifiedTime,webViewLink,parents),removed)",
                includeRemoved=True,
            )
            .execute()
        )
        changes.extend(response.get("changes", []))
        if "newStartPageToken" in response:
            new_token = response["newStartPageToken"]
            page_token = None
        else:
            page_token = response.get("nextPageToken")
            new_token = page_token

    return changes, new_token

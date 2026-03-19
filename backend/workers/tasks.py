"""Celery tasks for document ingestion and vector management."""

import hashlib
import logging
import os
from pathlib import Path

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="process_file", bind=True, max_retries=3)
def process_file_task(self, file_id: str, tenant_id: int = None, organization_id: int = None, user_id: int = None, access_token: str = None, refresh_token: str = None, expiry=None):
    """Download, parse, chunk, embed, and store a Drive file.

    This is the main ingestion pipeline task.
    """
    from drive.client import download_file, get_folder_path, _get_drive_service
    from app.integrations.google import build_drive_service
    from services.parser import parse_document
    from services.chunker import chunk_text
    from services.embeddings import generate_embeddings
    from rag.retriever import upsert_vectors, delete_by_file_id

    local_path = None
    try:
        logger.info(f"Processing file: {file_id}")

        # Step 1: Build installation-specific Drive service (OAuth) or fallback to service account
        drive_service = None
        if access_token and refresh_token:
            drive_service, creds, refreshed = build_drive_service(
                access_token, refresh_token, expiry)
            # If refresh occurred we can later update persisted db values, but this task is asynchronous.

        local_path, file_meta = download_file(file_id, service=drive_service)
        logger.info(f"Downloaded: {file_meta.get('name')} -> {local_path}")

        # Step 2: Parse
        text = parse_document(local_path)
        if not text.strip():
            logger.warning(f"No text extracted from {file_meta.get('name')}")
            return {"status": "skipped", "reason": "no text content"}

        # Step 3: Resolve folder path
        try:
            service_for_meta = drive_service or _get_drive_service()
            folder_path = get_folder_path(service_for_meta, file_meta)
        except Exception:
            folder_path = "/"

        # Step 4: Prepare metadata
        # Google Drive returns 'size' as a string, convert to int
        raw_size = file_meta.get("size")
        file_size = int(raw_size) if raw_size and raw_size.isdigit() else 0

        metadata = {
            "tenant_id": tenant_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "file_name": file_meta.get("name", "unknown"),
            "drive_file_id": file_id,
            "drive_link": file_meta.get("webViewLink", ""),
            "folder_path": folder_path,
            "file_size": file_size,
            "created_time": file_meta.get("createdTime", ""),
            "modified_time": file_meta.get("modifiedTime", ""),
        }

        # Step 5: Persist document metadata in SQL database
        try:
            from app.db.session import async_session_local
            from app.models import Document

            async def save_doc():
                async with async_session_local() as session:
                    doc = Document(
                        tenant_id=tenant_id or 0,
                        organization_id=organization_id or 0,
                        user_id=user_id,
                        drive_file_id=file_id,
                        name=file_meta.get("name", "unknown"),
                        mime_type=file_meta.get("mimeType", ""),
                        size=file_size,
                        drive_link=file_meta.get("webViewLink", ""),
                        doc_metadata=metadata,
                        modified_at=file_meta.get("modifiedTime", None),
                    )
                    session.add(doc)
                    await session.commit()
                    await session.refresh(doc)
                    return doc

            doc_entity = None
            import asyncio
            try:
                doc_entity = asyncio.get_event_loop().run_until_complete(save_doc())
                logger.info(f"Saved document metadata to DB: {file_id}")
            except Exception as db_err:
                logger.error(f"Failed to save document metadata to DB for {file_id}: {db_err}", exc_info=True)
                doc_entity = None
        except Exception as e:
            logger.error(f"Critical error in database save block for {file_id}: {e}", exc_info=True)
            doc_entity = None

        # Step 6: Chunk
        nodes = chunk_text(text, metadata=metadata)

        if not nodes:
            logger.warning(f"No chunks generated for {file_meta.get('name')}")
            return {"status": "skipped", "reason": "no chunks generated"}

        # Step 6: Delete existing vectors for this file (supports updates)
        delete_by_file_id(file_id)

        # Step 7: Generate embeddings in batches
        texts = [node.text for node in nodes]
        embeddings = generate_embeddings(texts)

        # Step 8: Prepare payloads and IDs
        payloads = []
        ids = []
        for i, node in enumerate(nodes):
            chunk_id = hashlib.md5(f"{file_id}_{i}".encode()).hexdigest()
            payload = {
                **metadata,
                "text": node.text,
                "chunk_index": i,
            }
            payloads.append(payload)
            ids.append(chunk_id)

        # Step 9: Upsert to Qdrant
        upsert_vectors(embeddings, payloads, ids)

        logger.info(
            f"Successfully indexed {len(nodes)} chunks for: {file_meta.get('name')}"
        )
        return {
            "status": "success",
            "file_name": file_meta.get("name"),
            "chunks": len(nodes),
        }

    except Exception as e:
        logger.error(f"Error processing file {file_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=30)

    finally:
        # Step 10: Clean up temp file
        if local_path and os.path.exists(local_path):
            os.unlink(local_path)
            logger.debug(f"Cleaned up temp file: {local_path}")


@celery_app.task(name="delete_file_vectors")
def delete_file_vectors_task(file_id: str):
    """Remove all vectors for a deleted/trashed file."""
    from rag.retriever import delete_by_file_id

    logger.info(f"Deleting vectors for file: {file_id}")
    delete_by_file_id(file_id)
    return {"status": "deleted", "file_id": file_id}


@celery_app.task(name="sync_tenant_files")
def sync_tenant_files_task(tenant_id: int):
    """List all files in monitored folders for a tenant and process each."""
    from app.db.session import async_session_local
    from app.models import GoogleIntegration
    from sqlalchemy.future import select
    from drive.client import list_all_files
    from app.integrations.google import build_drive_service
    import asyncio

    async def get_integration():
        async with async_session_local() as db:
            result = await db.execute(select(GoogleIntegration).where(GoogleIntegration.tenant_id == tenant_id))
            return result.scalars().first()

    integration = asyncio.get_event_loop().run_until_complete(get_integration())
    if not integration:
        logger.error(f"No Google integration found for tenant {tenant_id}")
        return {"status": "error", "message": "Integration not found"}

    logger.info(f"Starting sync for tenant {tenant_id}...")
    
    drive_service, creds, _ = build_drive_service(
        integration.access_token,
        integration.refresh_token,
        integration.expiry
    )

    folders = integration.monitored_folders or []
    if not folders:
        logger.info(f"No monitored folders for tenant {tenant_id}. Skipping sync.")
        return {"status": "skipped", "message": "No folders monitored"}

    all_files = []
    for folder_id in folders:
        try:
            folder_files = list_all_files(folder_id=folder_id, service=drive_service)
            all_files.extend(folder_files)
        except Exception as e:
            logger.error(f"Error listing files in folder {folder_id}: {e}")

    # Deduplicate files by ID
    unique_files = {f["id"]: f for f in all_files}.values()
    logger.info(f"Found {len(unique_files)} unique files to sync for tenant {tenant_id}")

    for f in unique_files:
        if f.get("mimeType") == "application/vnd.google-apps.folder":
            continue
            
        process_file_task.delay(
            f["id"],
            tenant_id=tenant_id,
            access_token=creds.token,
            refresh_token=creds.refresh_token or integration.refresh_token,
            expiry=creds.expiry
        )

    return {"status": "sync_started", "total_files": len(unique_files)}

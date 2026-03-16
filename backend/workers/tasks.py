"""Celery tasks for document ingestion and vector management."""

import hashlib
import logging
import os
from pathlib import Path

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="process_file", bind=True, max_retries=3)
def process_file_task(self, file_id: str):
    """Download, parse, chunk, embed, and store a Drive file.

    This is the main ingestion pipeline task.
    """
    from drive.client import download_file, get_folder_path, _get_drive_service
    from services.parser import parse_document
    from services.chunker import chunk_text
    from services.embeddings import generate_embeddings
    from rag.retriever import upsert_vectors, delete_by_file_id

    local_path = None
    try:
        logger.info(f"Processing file: {file_id}")

        # Step 1: Download
        local_path, file_meta = download_file(file_id)
        logger.info(f"Downloaded: {file_meta.get('name')} -> {local_path}")

        # Step 2: Parse
        text = parse_document(local_path)
        if not text.strip():
            logger.warning(f"No text extracted from {file_meta.get('name')}")
            return {"status": "skipped", "reason": "no text content"}

        # Step 3: Resolve folder path
        try:
            service = _get_drive_service()
            folder_path = get_folder_path(service, file_meta)
        except Exception:
            folder_path = "/"

        # Step 4: Prepare metadata
        # Google Drive returns 'size' as a string, convert to int
        raw_size = file_meta.get("size")
        file_size = int(raw_size) if raw_size and raw_size.isdigit() else 0
        
        metadata = {
            "file_name": file_meta.get("name", "unknown"),
            "drive_file_id": file_id,
            "drive_link": file_meta.get("webViewLink", ""),
            "folder_path": folder_path,
            "file_size": file_size,
            "created_time": file_meta.get("createdTime", ""),
            "modified_time": file_meta.get("modifiedTime", ""),
        }

        # Step 5: Chunk
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


@celery_app.task(name="sync_all_files")
def sync_all_files_task():
    """Full sync: list all files in configured folder and process each."""
    from drive.client import list_all_files

    logger.info("Starting full sync of all files...")
    files = list_all_files()
    logger.info(f"Found {len(files)} files to sync")

    for f in files:
        file_id = f.get("id")
        mime = f.get("mimeType", "")

        # Skip Google Drive folders
        if mime == "application/vnd.google-apps.folder":
            continue

        process_file_task.delay(file_id)

    return {"status": "sync_started", "total_files": len(files)}

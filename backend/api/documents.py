"""Document listing and sync status endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from rag.retriever import delete_by_file_id, get_collection_stats, get_indexed_files

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/documents")
async def list_documents():
    """List all indexed documents with metadata."""
    files = get_indexed_files()
    return {
        "total": len(files),
        "documents": files,
    }


@router.delete("/documents/{drive_file_id}")
async def delete_document(drive_file_id: str):
    """Delete an indexed file from the vector store."""
    try:
        delete_by_file_id(drive_file_id)
        return {"status": "deleted", "drive_file_id": drive_file_id}
    except Exception as e:
        logger.error(
            f"Failed to delete document {drive_file_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-status")
async def sync_status():
    """Show indexing statistics."""
    stats = get_collection_stats()
    files = get_indexed_files()

    return {
        "total_documents": len(files),
        "total_vectors": stats.get("total_vectors", 0),
        "vector_db_status": stats.get("status", "unknown"),
        "last_checked": datetime.utcnow().isoformat(),
    }

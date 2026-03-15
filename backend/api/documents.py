"""Document listing and sync status endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter

from rag.retriever import get_collection_stats, get_indexed_files

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

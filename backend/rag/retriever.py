"""Qdrant vector store integration for document retrieval."""

import logging
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from config.settings import get_settings
from services.embeddings import generate_query_embedding

logger = logging.getLogger(__name__)

_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """Get or create a Qdrant client singleton."""
    global _qdrant_client
    if _qdrant_client is None:
        settings = get_settings()
        _qdrant_client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        _ensure_collection(settings)
    return _qdrant_client


def _ensure_collection(settings) -> None:
    """Create the vector collection if it doesn't exist."""
    client = _qdrant_client
    collections = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in collections:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )
        logger.info(f"Created Qdrant collection: {settings.qdrant_collection}")


def upsert_vectors(
    vectors: list[list[float]],
    payloads: list[dict],
    ids: list[str],
) -> None:
    """Insert or update vectors in Qdrant.

    Args:
        vectors: List of embedding vectors.
        payloads: List of metadata dicts for each vector.
        ids: List of unique point IDs.
    """
    settings = get_settings()
    client = get_qdrant_client()

    points = [
        PointStruct(
            id=point_id,
            vector=vector,
            payload=payload,
        )
        for point_id, vector, payload in zip(ids, vectors, payloads)
    ]

    # Batch upsert in chunks of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=settings.qdrant_collection, points=batch)

    logger.info(f"Upserted {len(points)} vectors to Qdrant")


def search_vectors(query: str, top_k: Optional[int] = None) -> list[dict]:
    """Search for relevant document chunks.

    Args:
        query: The user's question.
        top_k: Number of results to return.

    Returns:
        List of results with score, text, and metadata.
    """
    settings = get_settings()
    client = get_qdrant_client()
    k = top_k or settings.top_k

    query_vector = generate_query_embedding(query)

    results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=k,
        with_payload=True,
    )

    return [
        {
            "score": hit.score,
            "text": hit.payload.get("text", ""),
            "metadata": {
                "file_name": hit.payload.get("file_name", ""),
                "drive_file_id": hit.payload.get("drive_file_id", ""),
                "drive_link": hit.payload.get("drive_link", ""),
                "folder_path": hit.payload.get("folder_path", ""),
                "created_time": hit.payload.get("created_time", ""),
                "modified_time": hit.payload.get("modified_time", ""),
                "chunk_index": hit.payload.get("chunk_index", 0),
            },
        }
        for hit in results
    ]


def delete_by_file_id(drive_file_id: str) -> None:
    """Delete all vectors associated with a Drive file ID."""
    settings = get_settings()
    client = get_qdrant_client()

    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="drive_file_id",
                    match=MatchValue(value=drive_file_id),
                )
            ]
        ),
    )
    logger.info(f"Deleted vectors for file: {drive_file_id}")


def get_collection_stats() -> dict:
    """Get collection statistics."""
    settings = get_settings()
    try:
        client = get_qdrant_client()
        info = client.get_collection(settings.qdrant_collection)
        return {
            "total_vectors": info.points_count,
            "status": info.status.value if info.status else "unknown",
        }
    except Exception:
        return {"total_vectors": 0, "status": "unavailable"}


def get_indexed_files() -> list[dict]:
    """Get a list of unique indexed files from Qdrant payloads."""
    settings = get_settings()
    try:
        client = get_qdrant_client()

        # Scroll through all points and collect unique file IDs
        files = {}
        offset = None
        while True:
            results, next_offset = client.scroll(
                collection_name=settings.qdrant_collection,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in results:
                fid = point.payload.get("drive_file_id", "")
                if fid and fid not in files:
                    files[fid] = {
                        "file_name": point.payload.get("file_name", ""),
                        "drive_file_id": fid,
                        "drive_link": point.payload.get("drive_link", ""),
                        "folder_path": point.payload.get("folder_path", ""),
                        "created_time": point.payload.get("created_time", ""),
                        "modified_time": point.payload.get("modified_time", ""),
                    }
            if next_offset is None:
                break
            offset = next_offset

        return list(files.values())
    except Exception:
        return []

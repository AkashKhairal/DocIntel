"""Qdrant vector store integration for document retrieval."""

import logging
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    PointStruct,
    SparseVector,
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
        _qdrant_client = QdrantClient(
            host=settings.qdrant_host, port=settings.qdrant_port)
        _ensure_collection(settings)
    return _qdrant_client


def _ensure_collection(settings) -> None:
    """Create the vector collection if it doesn't exist."""
    client = _qdrant_client
    collections = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in collections:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config={"dense": VectorParams(
                size=1024, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams(
                index=SparseIndexParams(on_disk=False))},
        )
        logger.info(
            f"Created Qdrant collection: {settings.qdrant_collection} with Hybrid Search enabled")


def upsert_vectors(
    vectors: list[dict],
    payloads: list[dict],
    ids: list[str],
) -> None:
    """Insert or update Hybrid vectors in Qdrant.

    Args:
        vectors: List of dictionaries containing 'dense' and 'sparse' vectors.
        payloads: List of metadata dicts for each vector.
        ids: List of unique point IDs.
    """
    settings = get_settings()
    client = get_qdrant_client()

    points = []
    for point_id, vector_dict, payload in zip(ids, vectors, payloads):

        # Format for Qdrant Hybrid schema
        vector_payload = {
            "dense": vector_dict["dense"],
            "sparse": SparseVector(
                indices=vector_dict["sparse"].indices.tolist(),
                values=vector_dict["sparse"].values.tolist(),
            )
        }

        points.append(
            PointStruct(
                id=point_id,
                vector=vector_payload,
                payload=payload,
            )
        )

    # Batch upsert in chunks of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i: i + batch_size]
        client.upsert(collection_name=settings.qdrant_collection, points=batch)

    logger.info(f"Upserted {len(points)} vectors to Qdrant")


def search_vectors(query: str, tenant_id: Optional[int] = None, top_k: Optional[int] = None) -> list[dict]:
    """Search for relevant document chunks using Hybrid queries.

    Args:
        query: The user's question.
        tenant_id: Tenant ID for isolation.
        top_k: Number of results to return.

    Returns:
        List of results with score, text, and metadata.
    """
    from qdrant_client.models import NamedVector, NamedSparseVector

    settings = get_settings()
    client = get_qdrant_client()
    k = top_k or settings.top_k

    query_vectors = generate_query_embedding(query)

    # In Qdrant 1.10+, we can use `query_points` with a `Prefetch` to do pure hybrid
    # For now, using standard search on the dense vector and relying on re-ranking later,
    # or doing a custom multi-vector search. Here is a basic hybrid attempt:
    from qdrant_client.models import Prefetch

    # Run a hybrid search relying on Reciprocal Rank Fusion via query_points
    query_kwargs = {
        "collection_name": settings.qdrant_collection,
        "prefetch": [
            Prefetch(
                query=query_vectors["dense"],
                using="dense",
                limit=k * 2,
            ),
            Prefetch(
                query=SparseVector(
                    indices=query_vectors["sparse"].indices.tolist(),
                    values=query_vectors["sparse"].values.tolist(),
                ),
                using="sparse",
                limit=k * 2,
            ),
        ],
        "query": query_vectors["dense"],  # Provide a fallback main query
        "using": "dense",
        "limit": k,
        "with_payload": True,
    }

    if tenant_id is not None:
        query_kwargs["filter"] = Filter(
            must=[
                FieldCondition(
                    key="tenant_id",
                    match=MatchValue(value=tenant_id),
                )
            ]
        )

    results = client.query_points(**query_kwargs).points

    return [
        {
            "score": hit.score,
            "text": hit.payload.get("text", ""),
            "metadata": {
                "file_name": hit.payload.get("file_name", ""),
                "drive_file_id": hit.payload.get("drive_file_id", ""),
                "drive_link": hit.payload.get("drive_link", ""),
                "folder_path": hit.payload.get("folder_path", ""),
                "file_size": hit.payload.get("file_size", 0),
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
                        "file_size": point.payload.get("file_size", 0),
                        "created_time": point.payload.get("created_time", ""),
                        "modified_time": point.payload.get("modified_time", ""),
                    }
            if next_offset is None:
                break
            offset = next_offset

        return list(files.values())
    except Exception:
        return []

"""Embedding generation using BAAI/bge-large-en-v1.5 via HuggingFace."""

import logging
from functools import lru_cache

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from fastembed import SparseTextEmbedding

from config.settings import get_settings

logger = logging.getLogger(__name__)

_embed_model = None
_sparse_embed_model = None


def get_embed_model() -> HuggingFaceEmbedding:
    """Get or create the embedding model singleton."""
    global _embed_model
    if _embed_model is None:
        settings = get_settings()
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _embed_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model,
            embed_batch_size=32,
        )
        logger.info("Embedding model loaded successfully")
    return _embed_model


def get_sparse_embed_model() -> SparseTextEmbedding:
    """Get or create the sparse embedding model singleton (BM25)."""
    global _sparse_embed_model
    if _sparse_embed_model is None:
        logger.info("Loading sparse embedding model: Qdrant/bm25")
        _sparse_embed_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        logger.info("Sparse embedding model loaded successfully")
    return _sparse_embed_model


def generate_embeddings(texts: list[str]) -> list[dict]:
    """Generate both dense and sparse embeddings for a batch of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of dictionaries containing 'dense' and 'sparse' vectors.
    """
    model = get_embed_model()
    sparse_model = get_sparse_embed_model()

    # Generate Dense (bge-large)
    dense_embeddings = model.get_text_embedding_batch(texts, show_progress=False)
    
    # Generate Sparse (BM25)
    sparse_embeddings_generator = sparse_model.embed(texts, batch_size=32)
    sparse_embeddings = list(sparse_embeddings_generator)

    results = []
    for dense, sparse in zip(dense_embeddings, sparse_embeddings):
        results.append({
            "dense": dense,
            "sparse": sparse
        })

    logger.info(f"Generated {len(results)} hybrid embeddings")
    return results


def generate_query_embedding(query: str) -> dict:
    """Generate both dense and sparse embeddings for a single query."""
    model = get_embed_model()
    sparse_model = get_sparse_embed_model()
    
    dense = model.get_query_embedding(query)
    sparse = list(sparse_model.query_embed(query))[0]
    
    return {
        "dense": dense,
        "sparse": sparse
    }

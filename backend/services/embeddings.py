"""Embedding generation.

This module currently uses OpenAI embeddings by default to avoid pulling large
GPU/deep learning dependencies into the Docker image (e.g., torch, transformers,
triton, nvidia libraries).

If you want to use a HuggingFace model locally, set `embedding_model` in config
to a HF model (e.g. "BAAI/bge-large-en-v1.5") and add the corresponding
dependencies back into requirements.
"""

import logging
from functools import lru_cache

from openai import OpenAI
from fastembed import SparseTextEmbedding

from config.settings import get_settings

logger = logging.getLogger(__name__)

_openai_client: OpenAI | None = None
_sparse_embed_model = None
_dense_embed_model = None


def get_openai_client() -> OpenAI:
    """Get or create the OpenAI client singleton."""
    global _openai_client
    if _openai_client is None:
        settings = get_settings()
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def get_sparse_embed_model() -> SparseTextEmbedding:
    """Get or create the sparse embedding model singleton (BM25)."""
    global _sparse_embed_model
    if _sparse_embed_model is None:
        logger.info("Loading sparse embedding model: prithivida/Splade_PP_en_v1")
        _sparse_embed_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")
        logger.info("Sparse embedding model loaded successfully")
    return _sparse_embed_model


def get_dense_embed_model():
    """Get or create the local dense embedding model singleton."""
    global _dense_embed_model
    if _dense_embed_model is None:
        from fastembed import TextEmbedding
        settings = get_settings()
        logger.info(f"Loading local dense embedding model: {settings.embedding_model}")
        _dense_embed_model = TextEmbedding(model_name=settings.embedding_model)
        logger.info("Local dense embedding model loaded successfully")
    return _dense_embed_model


def generate_embeddings(texts: list[str]) -> list[dict]:
    """Generate both dense and sparse embeddings for a batch of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of dictionaries containing 'dense' and 'sparse' vectors.
    """
    settings = get_settings()

    # Check if we should use local embeddings (FastEmbed)
    is_local = "/" in settings.embedding_model or not settings.openai_api_key

    if is_local:
        dense_model = get_dense_embed_model()
        dense_embeddings_generator = dense_model.embed(texts, batch_size=32)
        dense_embeddings = [list(e) for e in dense_embeddings_generator]
    else:
        client = get_openai_client()
        # Generate Dense embeddings using OpenAI
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
        dense_embeddings = [item.embedding for item in response.data]

    # Generate Sparse (BM25)
    sparse_model = get_sparse_embed_model()
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
    settings = get_settings()
    is_local = "/" in settings.embedding_model or not settings.openai_api_key

    if is_local:
        dense_model = get_dense_embed_model()
        dense = list(next(dense_model.embed([query])))
    else:
        client = get_openai_client()
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=query,
        )
        dense = response.data[0].embedding

    sparse_model = get_sparse_embed_model()
    sparse = list(sparse_model.query_embed(query))[0]

    return {
        "dense": dense,
        "sparse": sparse
    }

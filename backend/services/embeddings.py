"""Embedding generation using BAAI/bge-large-en-v1.5 via HuggingFace."""

import logging
from functools import lru_cache

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from config.settings import get_settings

logger = logging.getLogger(__name__)

_embed_model = None


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


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors.
    """
    model = get_embed_model()
    embeddings = model.get_text_embedding_batch(texts, show_progress=True)
    logger.info(f"Generated {len(embeddings)} embeddings")
    return embeddings


def generate_query_embedding(query: str) -> list[float]:
    """Generate an embedding for a single query."""
    model = get_embed_model()
    return model.get_query_embedding(query)

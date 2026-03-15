"""Token-based document chunking using LlamaIndex's SentenceSplitter."""

import logging
from typing import Optional

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document as LIDocument, TextNode

from config.settings import get_settings

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    metadata: Optional[dict] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[TextNode]:
    """Split text into overlapping chunks.

    Args:
        text: The full document text.
        metadata: Metadata to attach to each chunk.
        chunk_size: Override default chunk size (tokens).
        chunk_overlap: Override default chunk overlap (tokens).

    Returns:
        List of TextNode objects with metadata.
    """
    settings = get_settings()
    size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    splitter = SentenceSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
    )

    document = LIDocument(text=text, metadata=metadata or {})
    nodes = splitter.get_nodes_from_documents([document])

    logger.info(f"Chunked document into {len(nodes)} chunks (size={size}, overlap={overlap})")
    return nodes

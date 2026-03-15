"""Chat pipeline: retrieval-augmented generation with anti-hallucination."""

import json
import logging
from typing import AsyncGenerator, Optional

from config.settings import get_settings
from rag.retriever import search_vectors

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful document assistant for an enterprise. You answer questions ONLY using the provided document context.

STRICT RULES:
1. You must answer ONLY using the provided context from company documents.
2. If the answer is not present in the documents, respond exactly: "I could not find this information in the company documents."
3. NEVER make up information or use knowledge outside the provided context.
4. Always cite the source documents used in your answer.
5. Be precise, professional, and concise.

When citing sources, format them as:
Source: [filename] (if page info available, include it)
"""


def _build_context(results: list[dict]) -> tuple[str, list[dict]]:
    """Build context string and source list from search results."""
    if not results:
        return "", []

    context_parts = []
    sources = []
    seen_files = set()

    for i, r in enumerate(results):
        meta = r["metadata"]
        context_parts.append(
            f"[Document {i+1}: {meta['file_name']}]\n{r['text']}\n"
        )
        if meta["drive_file_id"] not in seen_files:
            seen_files.add(meta["drive_file_id"])
            sources.append({
                "file_name": meta["file_name"],
                "drive_link": meta["drive_link"],
                "drive_file_id": meta["drive_file_id"],
                "folder_path": meta["folder_path"],
            })

    return "\n---\n".join(context_parts), sources


async def chat_stream(question: str) -> AsyncGenerator[str, None]:
    """Stream a response for the given question using RAG.

    Yields:
        JSON-encoded chunks: {"type": "text", "content": "..."} or
        {"type": "sources", "content": [...]}
    """
    settings = get_settings()

    # Step 1: Retrieve relevant chunks
    results = search_vectors(question)
    context, sources = _build_context(results)

    if not context:
        yield json.dumps({"type": "text", "content": "I could not find this information in the company documents."})
        yield json.dumps({"type": "sources", "content": []})
        return

    # Step 2: Build messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context from company documents:\n\n{context}\n\n---\n\nQuestion: {question}",
        },
    ]

    # Step 3: Stream LLM response
    if settings.use_ollama:
        async for chunk in _stream_ollama(messages, settings):
            yield chunk
    else:
        async for chunk in _stream_openai(messages, settings):
            yield chunk

    # Step 4: Send source citations
    yield json.dumps({"type": "sources", "content": sources})


async def _stream_openai(messages: list[dict], settings) -> AsyncGenerator[str, None]:
    """Stream response from OpenAI API."""
    from openai import AsyncOpenAI

    if not settings.openai_api_key:
        yield json.dumps({"type": "text", "content": "Error: OpenAI API key not configured. Please set it in Settings."})
        return

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        stream = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            stream=True,
            temperature=0.1,
            max_tokens=2048,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield json.dumps({"type": "text", "content": chunk.choices[0].delta.content})

    except Exception as e:
        logger.error(f"OpenAI streaming error: {e}", exc_info=True)
        yield json.dumps({"type": "text", "content": f"Error communicating with LLM: {str(e)}"})


async def _stream_ollama(messages: list[dict], settings) -> AsyncGenerator[str, None]:
    """Stream response from Ollama (local LLM)."""
    import httpx

    url = f"{settings.ollama_base_url}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0.1},
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line.strip():
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield json.dumps({"type": "text", "content": content})
    except Exception as e:
        logger.error(f"Ollama streaming error: {e}", exc_info=True)
        yield json.dumps({"type": "text", "content": f"Error communicating with local LLM: {str(e)}"})

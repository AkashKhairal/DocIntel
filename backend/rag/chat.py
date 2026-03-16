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


async def _apply_reranking(query: str, results: list[dict], settings) -> list[dict]:
    """Re-rank retrieved Qdrant chunks using Cohere's cross-encoder model."""
    if not settings.cohere_api_key or not results:
        return results[:settings.rerank_top_k]
    
    import httpx
    
    url = "https://api.cohere.ai/v1/rerank"
    headers = {
        "Authorization": f"Bearer {settings.cohere_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Extract just the raw text strings for the Cohere API
    documents = [r["text"] for r in results]
    
    payload = {
        "model": "rerank-english-v3.0",
        "query": query,
        "documents": documents,
        "top_n": settings.rerank_top_k,
        "return_documents": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                body = response.json()
                ranked_indices = [item["index"] for item in body.get("results", [])]
                
                # Reconstruct the results array in the new sorted order
                reranked_results = [results[i] for i in ranked_indices]
                logger.info(f"Successfully re-ranked {len(results)} chunks to {len(reranked_results)}")
                return reranked_results
            else:
                logger.error(f"Cohere API Error {response.status_code}: {response.text}")
                return results[:settings.rerank_top_k]
    except Exception as e:
        logger.error(f"Failed to communicate with Cohere API: {e}")
        return results[:settings.rerank_top_k]


async def chat_stream(question: str) -> AsyncGenerator[str, None]:
    """Stream a response for the given question using RAG.

    Yields:
        JSON-encoded chunks: {"type": "text", "content": "..."} or
        {"type": "sources", "content": [...]}
    """
    settings = get_settings()

    # Step 1: Retrieve relevant chunks (Hybrid Search returns top_k=20)
    results = search_vectors(question)
    
    # Step 2: Cross-Encoder Re-ranking
    reranked_results = await _apply_reranking(question, results, settings)
    
    # Step 3: Build Context from the surviving top 5 chunks
    context, sources = _build_context(reranked_results)

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
    # Prioritize Ollama -> Gemini -> OpenAI
    if settings.use_ollama:
        async for chunk in _stream_ollama(messages, settings):
            yield chunk
    elif settings.gemini_api_key:
        async for chunk in _stream_gemini(messages, settings):
            yield chunk
    elif settings.openai_api_key:
        async for chunk in _stream_openai(messages, settings):
            yield chunk
    else:
        yield json.dumps({"type": "text", "content": "Error: No LLM configured. Please provide an OpenAI or Gemini API key in Settings."})

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


async def _stream_gemini(messages: list[dict], settings) -> AsyncGenerator[str, None]:
    """Stream response from Gemini API."""
    import httpx

    if not settings.gemini_api_key:
        yield json.dumps({"type": "text", "content": "Error: Gemini API key not configured. Please set it in Settings."})
        return

    # Convert generic messages format to Google Gemini API format
    contents = []
    system_instruction = None

    for m in messages:
        if m["role"] == "system":
            system_instruction = {"parts": [{"text": m["content"]}]}
        elif m["role"] == "user":
            contents.append({"role": "user", "parts": [{"text": m["content"]}]})
        elif m["role"] == "assistant":
            contents.append({"role": "model", "parts": [{"text": m["content"]}]})

    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.1},
    }
    if system_instruction:
        payload["systemInstruction"] = system_instruction

    # Use the streaming endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:streamGenerateContent?key={settings.gemini_api_key}"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"Gemini API error: {response.status_code} - {error_text}")
                    yield json.dumps({"type": "text", "content": "Error: Failed to fetch response from Gemini API."})
                    return

                # Read JSON Server-Sent Events stream from Gemini API
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    # Gemini streams a large JSON array. We need to extract the individual objects.
                    # A naive but effective way is to look for complete candidates objects.
                    
                    # Find all complete "candidates" blocks in the current buffer
                    while True:
                        try:
                             # This is a bit hacky, but standard streaming parsers for this format
                             # look for the "candidates" key and extract the text. Since it's a JSON array,
                             # we can try to extract JSON objects if we can find matching braces.
                             
                             # Let's find the first '{'
                             start_idx = buffer.find('{')
                             if start_idx == -1:
                                 break
                                 
                             # Now let's try to parse a JSON object from this start index
                             # We'll try different end indices until json.loads succeeds
                             parsed_obj = None
                             end_idx = start_idx + 1
                             
                             # Simple brace matching to find the likely end of the object
                             brace_count = 0
                             for i, char in enumerate(buffer[start_idx:]):
                                 if char == '{':
                                     brace_count += 1
                                 elif char == '}':
                                     brace_count -= 1
                                     
                                 if brace_count == 0:
                                     # Found a complete object
                                     end_idx = start_idx + i + 1
                                     try:
                                         parsed_obj = json.loads(buffer[start_idx:end_idx])
                                         
                                         # Process the object
                                         candidates = parsed_obj.get("candidates", [])
                                         if candidates:
                                             parts = candidates[0].get("content", {}).get("parts", [])
                                             if parts and "text" in parts[0]:
                                                 # Yield it immediately
                                                 logger.info(f"Yielding: {parts[0]['text']}")
                                                 yield json.dumps({"type": "text", "content": parts[0]["text"]})
                                                 
                                         # Remove processed part from buffer
                                         buffer = buffer[end_idx:]
                                         break # Break inner loop, continue `while True` to check buffer again
                                         
                                     except json.JSONDecodeError:
                                         # Not a valid JSON object yet, continue searching
                                         pass
                                         
                             if parsed_obj is None:
                                 # Incomplete object in buffer, wait for more chunks
                                 break
                             
                        except Exception as e:
                            logger.error(f"Error parsing Gemini chunk: {e}")
                            break
                            
    except Exception as e:
        logger.error(f"Gemini streaming error: {e}", exc_info=True)
        yield json.dumps({"type": "text", "content": f"Error communicating with Gemini: {str(e)}"})

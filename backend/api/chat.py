"""Chat API endpoint with streaming responses."""

import logging

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config.settings import get_settings
from rag.chat import chat_stream

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
async def chat(
    request: ChatRequest,
    x_api_key: str = Header(default="", alias="X-API-Key"),
):
    """Send a question and get a streamed answer with source citations.

    Requires X-API-Key header if API_KEY is configured.
    """
    settings = get_settings()

    # API key auth (skip if not configured)
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    async def event_generator():
        async for chunk in chat_stream(request.question):
            yield chunk + "\n"

    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson",
    )

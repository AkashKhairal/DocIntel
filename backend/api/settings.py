"""Settings API for managing credentials and configuration via the UI."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from config.settings import get_settings, save_runtime_config

logger = logging.getLogger(__name__)

router = APIRouter()


class SettingsUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    webhook_url: Optional[str] = None
    google_credentials_json: Optional[str] = None
    google_drive_folder_id: Optional[str] = None
    use_ollama: Optional[bool] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    cohere_api_key: Optional[str] = None


@router.get("/settings")
async def get_current_settings():
    """Return current config status (masks secret values)."""
    settings = get_settings()

    return {
        "has_openai_key": bool(settings.openai_api_key),
        "has_gemini_key": bool(settings.gemini_api_key),
        "has_cohere_key": bool(settings.cohere_api_key),
        "has_google_creds": bool(settings.google_credentials_json),
        "webhook_url": settings.webhook_url,
        "google_drive_folder_id": settings.google_drive_folder_id or "",
        "use_ollama": settings.use_ollama,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
        "gemini_model": settings.gemini_model,
        "embedding_model": settings.embedding_model,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
    }


@router.post("/settings")
async def update_settings(update: SettingsUpdate):
    """Update application settings at runtime.

    Accepts Google OAuth credentials JSON, OpenAI API key,
    webhook endpoint URL, and other config options.
    """
    data = {}

    if update.openai_api_key is not None:
        data["openai_api_key"] = update.openai_api_key

    if update.webhook_url is not None:
        data["webhook_url"] = update.webhook_url

    if update.cohere_api_key is not None:
        data["cohere_api_key"] = update.cohere_api_key
        
    if update.google_credentials_json is not None:
        # Validate that it's valid JSON
        try:
            json.loads(update.google_credentials_json)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid Google credentials JSON format",
            )
        data["google_credentials_json"] = update.google_credentials_json

    if update.google_drive_folder_id is not None:
        data["google_drive_folder_id"] = update.google_drive_folder_id

    if update.use_ollama is not None:
        data["use_ollama"] = update.use_ollama

    if update.ollama_base_url is not None:
        data["ollama_base_url"] = update.ollama_base_url

    if update.ollama_model is not None:
        data["ollama_model"] = update.ollama_model

    if update.gemini_api_key is not None:
        data["gemini_api_key"] = update.gemini_api_key

    if update.gemini_model is not None:
        data["gemini_model"] = update.gemini_model

    if not data:
        raise HTTPException(status_code=400, detail="No settings to update")

    save_runtime_config(data)
    logger.info(f"Settings updated: {list(data.keys())}")

    return {"status": "success", "updated_keys": list(data.keys())}


@router.post("/settings/upload-credentials")
async def upload_google_credentials(file: UploadFile = File(...)):
    """Upload a Google OAuth/Service Account credentials JSON file."""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="File must be a .json file")

    content = await file.read()
    try:
        creds = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    # Basic validation
    if "type" not in creds:
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials file: missing 'type' field",
        )

    save_runtime_config({"google_credentials_json": content.decode("utf-8")})
    logger.info("Google credentials uploaded successfully")

    return {
        "status": "success",
        "credential_type": creds.get("type"),
        "project_id": creds.get("project_id", ""),
    }


@router.post("/settings/setup-webhook")
async def setup_drive_webhook():
    """Initialize the Google Drive watch channel for push notifications."""
    settings = get_settings()

    if not settings.google_credentials_json:
        raise HTTPException(
            status_code=400,
            detail="Google credentials not configured. Upload them first.",
        )

    if not settings.webhook_url:
        raise HTTPException(
            status_code=400,
            detail="Webhook URL not configured. Set it in Settings first.",
        )

    try:
        from drive.client import setup_watch_channel
        from drive.webhook import _save_page_token

        result = setup_watch_channel()
        _save_page_token(result["start_page_token"])

        return {
            "status": "success",
            "channel_id": result["channel_id"],
            "expiration": result["expiration"],
        }
    except Exception as e:
        logger.error(f"Failed to setup webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/trigger-sync")
async def trigger_full_sync():
    """Trigger a full sync of all files in the configured Drive folder."""
    settings = get_settings()

    if not settings.google_credentials_json:
        raise HTTPException(
            status_code=400,
            detail="Google credentials not configured.",
        )

    try:
        from workers.tasks import sync_all_files_task

        result = sync_all_files_task.delay()
        return {"status": "sync_started", "task_id": str(result.id)}
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

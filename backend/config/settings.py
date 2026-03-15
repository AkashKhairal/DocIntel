"""Application settings loaded from environment variables and runtime config."""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


CONFIG_DIR = Path(__file__).parent.parent / "data"
RUNTIME_CONFIG_FILE = CONFIG_DIR / "runtime_config.json"


class Settings(BaseSettings):
    """Application settings with env var support and runtime overrides."""

    # --- App ---
    app_name: str = "DocIntel"
    api_key: str = Field(default="", description="API key for authenticating chat requests")
    debug: bool = False

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    # --- Ollama (optional local LLM) ---
    use_ollama: bool = False
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3"

    # --- Embedding ---
    embedding_model: str = "BAAI/bge-large-en-v1.5"

    # --- Qdrant ---
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "documents"

    # --- Redis / Celery ---
    redis_url: str = "redis://redis:6379/0"

    # --- Google Drive ---
    google_credentials_json: str = ""  # raw JSON string of service account creds
    google_drive_folder_id: str = ""  # root folder to watch
    webhook_url: str = ""  # public HTTPS URL for Drive push notifications

    # --- Chunking ---
    chunk_size: int = 500
    chunk_overlap: int = 100

    # --- Retrieval ---
    top_k: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def _load_runtime_config() -> dict:
    """Load runtime config overrides saved via the settings UI."""
    if RUNTIME_CONFIG_FILE.exists():
        try:
            return json.loads(RUNTIME_CONFIG_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_runtime_config(data: dict) -> None:
    """Persist runtime config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing = _load_runtime_config()
    existing.update(data)
    RUNTIME_CONFIG_FILE.write_text(json.dumps(existing, indent=2))
    # Bust the lru_cache so next call picks up new values
    get_settings.cache_clear()


def get_settings() -> Settings:
    """Return settings with runtime overrides applied."""
    runtime = _load_runtime_config()
    # Merge runtime config into env-based settings
    base = Settings()
    if runtime:
        overrides = {}
        for key, value in runtime.items():
            if hasattr(base, key) and value:
                overrides[key] = value
        if overrides:
            base = Settings(**overrides)
    return base

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
    api_key: str = Field(
        default="", description="API key for authenticating chat requests")
    debug: bool = False

    # --- OpenAI ---
    # OpenAI is deprecated for manual key entry on this deployment.
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    # --- Gemini ---
    gemini_api_key: str = Field("", env="GEMINI_API_KEY")
    gemini_model: str = "gemini-2.5-flash"

    # --- Ollama (optional local LLM) ---
    use_ollama: bool = False
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3"

    # --- Embedding ---
    # Use an OpenAI embedding model by default to avoid large local ML dependencies.
    # You can still use a HuggingFace model by setting this to a HF model path (e.g. "BAAI/bge-large-en-v1.5")
    embedding_model: str = "text-embedding-3-large"

    # --- Qdrant ---
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "documents"

    # --- Redis / Celery ---
    redis_url: str = "redis://redis:6379/0"

    # --- Google Drive ---
    # raw JSON string of service account creds (legacy)
    google_credentials_json: str = ""
    google_drive_folder_id: str = ""  # root folder to watch
    webhook_url: str = ""  # public HTTPS URL for Drive push notifications
    # e.g. https://app.example.com/integrations/google/callback
    google_oauth_redirect_uri: str = ""

    # --- Chunking ---
    chunk_size: int = 500
    chunk_overlap: int = 100

    # --- Retrieval ---
    top_k: int = 20  # Retrieve 20 for hybrid search
    rerank_top_k: int = 5  # Re-rank down to best 5
    cohere_api_key: str = ""

    class Config:
        env_file = str(Path(__file__).resolve().parents[2] / ".env")
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


@lru_cache
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

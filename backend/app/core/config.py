import json
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


CONFIG_DIR = Path(__file__).parent.parent.parent / "data"
RUNTIME_CONFIG_FILE = CONFIG_DIR / "runtime_config.json"


class Settings(BaseSettings):
    # App
    app_name: str = "DocIntel SaaS"
    api_key: str = Field("", env="API_KEY")
    debug: bool = False
    secret_key: str = Field("change-me", env="SECRET_KEY")
    access_token_expire_minutes: int = 60

    # Database
    database_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@postgres:5432/docintel", env="DATABASE_URL")

    # Redis
    redis_url: str = Field("redis://redis:6379/0", env="REDIS_URL")

    # Qdrant
    qdrant_host: str = Field("qdrant", env="QDRANT_HOST")
    qdrant_port: int = Field(6333, env="QDRANT_PORT")
    qdrant_collection_prefix: str = Field("tenant_")
    # Google OAuth
    google_client_id: str = Field("", env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field("", env="GOOGLE_CLIENT_SECRET")
    google_oauth_redirect_uri: str = Field(
        "http://localhost:8000/integrations/google/callback", env="GOOGLE_OAUTH_REDIRECT_URI")
    frontend_url: str = Field("http://localhost:3000", env="FRONTEND_URL")
    webhook_url: str = Field("", env="WEBHOOK_URL")
    google_drive_folder_id: str = Field("", env="GOOGLE_DRIVE_FOLDER_ID")
    google_credentials_json: str = Field("", env="GOOGLE_CREDENTIALS_JSON")

    # LLM Providers
    # OpenAI API key is no longer configurable via UI; disabled in this deployment.
    openai_api_key: str = ""
    openai_model: str = "gpt-4-mini"
    # Gemini API key must be runtime environment variable (GEMINI_API_KEY)
    gemini_api_key: str = Field("", env="GEMINI_API_KEY")
    gemini_model: str = "gemini-2.0-flash"
    cohere_api_key: str = ""
    use_ollama: bool = False
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3"

    # RAG Settings
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    chunk_size: int = 500
    chunk_overlap: int = 100
    top_k: int = 20
    rerank_top_k: int = 5
    qdrant_collection: str = "documents"

    class Config:
        env_file = str(Path(__file__).resolve().parents[3] / ".env")
        env_file_encoding = "utf-8"


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

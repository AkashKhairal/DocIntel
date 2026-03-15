"""Enterprise Document Intelligence System — FastAPI Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.chat import router as chat_router
from api.documents import router as documents_router
from api.settings import router as settings_router
from drive.webhook import router as webhook_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("🚀 DocIntel starting up...")
    # Ensure data directory exists
    from config.settings import CONFIG_DIR
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("✅ Application ready")
    yield
    logger.info("👋 DocIntel shutting down...")


app = FastAPI(
    title="DocIntel — Enterprise Document Intelligence",
    description="Chat with your company documents stored in Google Drive",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat_router, tags=["Chat"])
app.include_router(documents_router, tags=["Documents"])
app.include_router(settings_router, tags=["Settings"])
app.include_router(webhook_router, tags=["Webhook"])


@app.get("/")
async def root():
    return {
        "name": "DocIntel",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

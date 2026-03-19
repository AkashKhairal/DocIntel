"""Enterprise Document Intelligence System — FastAPI Application."""

from app.api.admin import router as admin_router
from app.api.users import router as users_router
from app.api.organizations import router as organizations_router
from app.api.tenants import router as tenants_router
import logging
from contextlib import asynccontextmanager

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.crud import get_password_hash
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import async_session_local, engine
from app.models.tenant import Tenant
from app.models.organization import Organization
from app.models.user import User

from api.chat import router as chat_router
from api.documents import router as documents_router
from api.settings import router as settings_router
from drive.webhook import router as webhook_router
from app.auth.routes import router as auth_router
from app.api.google_integrations import router as google_integrations_router
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.api_key import APIKey
from app.models.query import Query
from app.models.usage_log import UsageLog
from pathlib import Path  # Ensure Path is imported

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def truncate_password_to_bcrypt_limit(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) <= 72:
        return password
    # truncate bytes to bcrypt max (72) and decode safely
    return encoded[:72].decode("utf-8", errors="ignore")


async def create_master_account():
    settings = get_settings()
    master_email = os.getenv("MASTER_ADMIN_EMAIL", "admin@docintel.local")
    master_password = os.getenv("MASTER_ADMIN_PASSWORD", "Admin1234!")
    master_password = truncate_password_to_bcrypt_limit(master_password)
    tenant_name = os.getenv("MASTER_TENANT_NAME", "default-tenant")
    org_name = os.getenv("MASTER_ORG_NAME", "default-org")
    settings = get_settings()
    master_email = os.getenv("MASTER_ADMIN_EMAIL", "admin@docintel.local")
    master_password = os.getenv("MASTER_ADMIN_PASSWORD", "Admin1234!")
    master_password = truncate_password_to_bcrypt_limit(master_password)
    tenant_name = os.getenv("MASTER_TENANT_NAME", "default-tenant")
    org_name = os.getenv("MASTER_ORG_NAME", "default-org")

    async with async_session_local() as db:  # type: AsyncSession
        tenant_result = await db.execute(select(Tenant).where(Tenant.slug == tenant_name))
        tenant = tenant_result.scalars().first()
        if not tenant:
            tenant = Tenant(name="Default Tenant", slug=tenant_name)
            db.add(tenant)
            await db.commit()
            await db.refresh(tenant)

        org_result = await db.execute(select(Organization).where(Organization.tenant_id == tenant.id))
        org = org_result.scalars().first()
        if not org:
            org = Organization(tenant_id=tenant.id,
                               name="Default Organization")
            db.add(org)
            await db.commit()
            await db.refresh(org)

        user_result = await db.execute(select(User).where(User.email == master_email))
        existing_user = user_result.scalars().first()
        if not existing_user:
            hashed_password = get_password_hash(master_password)
            user = User(
                email=master_email,
                hashed_password=hashed_password,
                tenant_id=tenant.id,
                organization_id=org.id,
                role="admin",
            )
            db.add(user)
            await db.commit()
            logger.info(f"✅ Created master account: {master_email}")
        else:
            logger.info(f"✅ Master account exists: {master_email}")


# Ensure the database connection URL is correctly set
settings = get_settings()
if not settings.database_url:
    raise ValueError("DATABASE_URL environment variable is not set.")
logger.info(f"Using database URL: {settings.database_url}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("🚀 DocIntel starting up...")

    # Update the data directory path to use a local directory
    local_data_path = Path("./data")
    local_data_path.mkdir(parents=True, exist_ok=True)

    # Ensure DB schema exists (create tables if missing) as a one-time fallback.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await create_master_account()

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


app.include_router(auth_router)
app.include_router(tenants_router)
app.include_router(organizations_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(google_integrations_router, tags=["Google Integration"])
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

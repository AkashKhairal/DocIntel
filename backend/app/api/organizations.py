from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_tenant_context
from app.db.session import get_db
from app.models.organization import Organization

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/")
async def create_organization(name: str, tenant_context=Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    org = Organization(tenant_id=tenant_context["tenant_id"], name=name)
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


@router.get("/")
async def list_organizations(tenant_context=Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM organizations WHERE tenant_id = :tenant_id"), {"tenant_id": tenant_context["tenant_id"]})
    return {"organizations": result.mappings().all()}

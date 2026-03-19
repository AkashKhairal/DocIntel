from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_tenant_context
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.organization import Organization

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("/")
async def create_tenant(name: str, db: AsyncSession = Depends(get_db)):
    tenant = Tenant(name=name, slug=name.lower().replace(" ", "-"))
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.get("/me")
async def get_tenant(tenant_context=Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    tenant = await db.get(Tenant, tenant_context["tenant_id"])
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

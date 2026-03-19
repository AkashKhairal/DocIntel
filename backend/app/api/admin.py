from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_admin_user
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def admin_stats(admin_user=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    total_tenants = (await db.execute(select(func.count()).select_from(Tenant))).scalar_one()
    total_orgs = (await db.execute(select(func.count()).select_from(Organization))).scalar_one()
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    return {
        "total_tenants": total_tenants,
        "total_organizations": total_orgs,
        "total_users": total_users,
        "admin_user": admin_user.email,
    }


@router.get("/tenants")
async def list_tenants(admin_user=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = result.scalars().all()
    tenant_list = []
    for tenant in tenants:
        users_count_result = await db.execute(select(func.count()).select_from(User).where(User.tenant_id == tenant.id))
        users_count = users_count_result.scalar_one()
        tenant_list.append(
            {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "created_at": tenant.created_at,
                "status": tenant.status if hasattr(tenant, "status") else "active",
                "users": users_count,
            }
        )
    return tenant_list


@router.get("/tenants/{tenant_id}")
async def get_tenant_details(tenant_id: int, admin_user=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    orgs = (await db.execute(select(Organization).where(Organization.tenant_id == tenant.id))).scalars().all()
    users = (await db.execute(select(User).where(User.tenant_id == tenant.id))).scalars().all()
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "created_at": tenant.created_at,
        "status": getattr(tenant, "status", "active"),
        "organizations": [{"id": or_.id, "name": or_.name} for or_ in orgs],
        "users": [{"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active} for u in users],
    }


@router.post("/tenants")
async def create_tenant(payload: dict, admin_user=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    name = payload.get("name")
    owner_email = payload.get("owner_email")
    if not name or not owner_email:
        raise HTTPException(status_code=400, detail="name and owner_email are required")

    slug = name.strip().lower().replace(" ", "-")
    existing = await db.execute(select(Tenant).where(Tenant.slug == slug))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Tenant already exists")

    tenant = Tenant(name=name.strip(), slug=slug)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    org = Organization(tenant_id=tenant.id, name="Default Organization")
    db.add(org)
    await db.commit()
    await db.refresh(org)

    user = User(
        email=owner_email.strip(),
        hashed_password="",
        tenant_id=tenant.id,
        organization_id=org.id,
        role="admin",
        is_active=False,
    )
    db.add(user)
    await db.commit()

    return {
        "tenant": {"id": tenant.id, "name": tenant.name, "slug": tenant.slug},
        "organization": {"id": org.id, "name": org.name},
        "owner": {"id": user.id, "email": user.email, "role": user.role},
    }


@router.patch("/tenants/{tenant_id}")
async def update_tenant(tenant_id: int, payload: dict, admin_user=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if "name" in payload:
        tenant.name = payload["name"].strip()
        tenant.slug = tenant.name.lower().replace(" ", "-")

    if "status" in payload and hasattr(tenant, "status"):
        tenant.status = payload["status"]

    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    return {"id": tenant.id, "name": tenant.name, "slug": tenant.slug, "status": getattr(tenant, "status", "active")}

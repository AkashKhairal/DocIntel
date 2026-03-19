from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.future import select

from app.db.session import get_db
from app.auth.crud import get_user_by_email, create_user, verify_password
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserCreate, UserLogin, Token
from app.models.tenant import Tenant
from app.models.organization import Organization

router = APIRouter(prefix="/auth", tags=["auth"])


async def ensure_default_tenant_org(db: AsyncSession, tenant_id: int | None, organization_id: int | None):
    if tenant_id is not None and organization_id is not None:
        return tenant_id, organization_id

    default_tenant_slug = "default-tenant"
    tenant_stmt = select(Tenant).where(Tenant.slug == default_tenant_slug)
    tenant_result = await db.execute(tenant_stmt)
    tenant = tenant_result.scalars().first()
    if not tenant:
        tenant = Tenant(name="Default Tenant", slug=default_tenant_slug)
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)

    org_stmt = select(Organization).where(Organization.tenant_id == tenant.id)
    org_result = await db.execute(org_stmt)
    org = org_result.scalars().first()
    if not org:
        org = Organization(tenant_id=tenant.id, name="Default Organization")
        db.add(org)
        await db.commit()
        await db.refresh(org)

    return tenant.id, org.id


@router.post("/signup", response_model=Token)
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    tenant_id, organization_id = await ensure_default_tenant_org(db, payload.tenant_id, payload.organization_id)
    payload.tenant_id = tenant_id
    payload.organization_id = organization_id

    user = await create_user(db, payload)
    access_token = create_access_token(
        data={"user_id": user.id, "tenant_id": user.tenant_id, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(
        data={"user_id": user.id, "tenant_id": user.tenant_id, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "tenant_id": current_user.tenant_id,
        "organization_id": current_user.organization_id,
        "role": current_user.role,
    }

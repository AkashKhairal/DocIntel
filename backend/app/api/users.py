from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_tenant_context
from app.db.session import get_db
from app.models.user import User
from app.auth.crud import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/")
async def create_user(email: str, password: str, role: str = "viewer", tenant_context=Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    existing = await db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email})
    if existing.first():
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        tenant_id=tenant_context["tenant_id"],
        organization_id=tenant_context["organization_id"],
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/")
async def list_users(tenant_context=Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT id, email, role, is_active, created_at FROM users WHERE tenant_id = :tenant_id"), {"tenant_id": tenant_context["tenant_id"]})
    return {"users": result.mappings().all()}

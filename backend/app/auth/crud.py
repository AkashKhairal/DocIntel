from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext

from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    # bcrypt has a 72-byte password limit. Truncate safely at UTF-8 boundary.
    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        encoded = encoded[:72]
        password = encoded.decode("utf-8", errors="ignore")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, user_create):
    hashed_password = get_password_hash(user_create.password)
    user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        tenant_id=user_create.tenant_id,
        organization_id=user_create.organization_id,
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

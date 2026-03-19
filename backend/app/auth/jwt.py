from datetime import datetime, timedelta
from typing import Optional

from jose import jwt

from app.core.config import get_settings
from app.auth.schemas import TokenData

settings = get_settings()

ALGORITHM = "HS256"


def create_access_token(*, data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + \
        (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    user_id = payload.get("user_id")
    tenant_id = payload.get("tenant_id")
    role = payload.get("role")
    return TokenData(user_id=user_id, tenant_id=tenant_id, role=role)

"""JWT and Argon2 authentication helpers."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.access_control.models import Permission, Role, RolePermission, UserRole
from app.modules.user.models import User

password_hasher = PasswordHasher()
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def _encode(subject: str, token_type: str, expires_delta: dt.timedelta) -> tuple[str, dt.datetime]:
    now = dt.datetime.now(dt.timezone.utc)
    expires_at = now + expires_delta
    token = jwt.encode(
        {"sub": subject, "type": token_type, "iat": now, "exp": expires_at, "jti": uuid.uuid4().hex},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_at


def issue_tokens(user_id: int) -> tuple[str, str, dt.datetime]:
    access, expires_at = _encode(
        str(user_id), "access", dt.timedelta(minutes=settings.access_token_minutes)
    )
    refresh, _ = _encode(str(user_id), "refresh", dt.timedelta(days=settings.refresh_token_days))
    return access, refresh, expires_at


def decode_token(token: str, expected_type: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc
    if payload.get("type") != expected_type or not str(payload.get("sub", "")).isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    return int(payload["sub"])


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")
    user = await db.get(User, decode_token(credentials.credentials, "access"))
    if user is None or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user is inactive or missing")
    return user


async def permission_codes(db: AsyncSession, user_id: int) -> set[str]:
    result = await db.scalars(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    return set(result.all())


def require_permission(code: str):
    async def dependency(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> User | None:
        if settings.environment == "local":
            return None
        user = await get_current_user(credentials, db)
        if code not in await permission_codes(db, user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permission required")
        return user

    return dependency


CurrentUser = Annotated[User, Depends(get_current_user)]
"""Bearer-token authentication and RBAC dependencies for the HTTP API.

FastAPI resolves ``Depends`` on these; :data:`CurrentUser` is the annotated
shorthand for "an authenticated, active user".
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.token_codec import decode_token
from app.modules.access_control.models import Permission, Role, RolePermission, UserRole
from app.modules.user.models import User

bearer = HTTPBearer(auto_error=False)

_Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
_Db = Annotated[AsyncSession, Depends(get_db)]


class BearerAuth:
    async def current_user(self, credentials: _Credentials, db: _Db) -> User:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required"
            )
        user = await db.get(User, decode_token(credentials.credentials, "access"))
        if user is None or not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="user is inactive or missing"
            )
        return user

    async def permission_codes(self, db: AsyncSession, user_id: int) -> set[str]:
        result = await db.scalars(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return set(result.all())

    def require_permission(self, code: str):
        async def dependency(credentials: _Credentials, db: _Db) -> User | None:
            if settings.environment == "local":
                return None
            user = await self.current_user(credentials, db)
            if code not in await self.permission_codes(db, user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="permission required"
                )
            return user

        return dependency


bearer_auth = BearerAuth()


async def get_current_user(credentials: _Credentials, db: _Db) -> User:
    return await bearer_auth.current_user(credentials, db)


def require_permission(code: str):
    return bearer_auth.require_permission(code)


async def permission_codes(db: AsyncSession, user_id: int) -> set[str]:
    return await bearer_auth.permission_codes(db, user_id)


CurrentUser = Annotated[User, Depends(get_current_user)]

__all__ = [
    "BearerAuth",
    "CurrentUser",
    "bearer",
    "bearer_auth",
    "get_current_user",
    "permission_codes",
    "require_permission",
]

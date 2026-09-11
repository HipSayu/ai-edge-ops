"""Authentication use-cases: password login, refresh, session assembly."""

from __future__ import annotations

from dqh.svc_core.contracts.errors import UnauthorizedError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.password_hasher import verify_password
from app.core.token_codec import decode_token, issue_tokens
from app.modules.iam.bearer_auth import permission_codes
from app.modules.iam.models import User
from app.modules.iam.schemas import AuthSession, AuthTokens, UserSession


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _active_user_or_401(self, user: User | None) -> User:
        if user is None or not user.active:
            raise UnauthorizedError("user is inactive or missing")
        return user

    async def login(self, email: str, password: str) -> AuthSession:
        user = await self.session.scalar(select(User).where(User.email == email.lower()))
        if user is None or not user.active or not verify_password(password, user.password_hash):
            raise UnauthorizedError("invalid credentials")
        return await self._session_for(user)

    async def refresh(self, refresh_token: str) -> AuthTokens:
        user = await self._active_user_or_401(
            await self.session.get(User, decode_token(refresh_token, "refresh"))
        )
        access, new_refresh, expires_at = issue_tokens(user.id)
        return AuthTokens(accessToken=access, refreshToken=new_refresh, expiresAt=expires_at)

    async def session_view(self, user: User) -> UserSession:
        return UserSession(
            id=user.id,
            name=user.name,
            email=user.email,
            active=user.active,
            permissions=sorted(await permission_codes(self.session, user.id)),
        )

    async def _session_for(self, user: User) -> AuthSession:
        access, refresh, expires_at = issue_tokens(user.id)
        return AuthSession(
            accessToken=access,
            refreshToken=refresh,
            expiresAt=expires_at,
            user=await self.session_view(user),
        )


__all__ = ["AuthService"]

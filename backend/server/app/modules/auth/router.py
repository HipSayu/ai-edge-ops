from __future__ import annotations

from datetime import datetime

from dqh.svc_core.transports.http import ApiResponse, ok
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.bearer_auth import CurrentUser, permission_codes
from app.core.password_hasher import verify_password
from app.core.token_codec import decode_token, issue_tokens
from app.modules.auth.schemas import AuthSession, AuthTokens, LoginRequest, RefreshRequest, UserSession
from app.modules.user.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _session_payload(user: User, permissions: set[str], access: str, refresh: str, expires_at: datetime) -> AuthSession:
    return AuthSession(
        accessToken=access,
        refreshToken=refresh,
        expiresAt=expires_at,
        user=UserSession(
            id=user.id,
            name=user.name,
            email=user.email,
            active=user.active,
            permissions=sorted(permissions),
        ),
    )


@router.post("/login", response_model=ApiResponse[AuthSession])
async def login(data: LoginRequest, db: DbSession) -> ApiResponse[AuthSession]:
    user = await db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not user.active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    access, refresh, expires_at = issue_tokens(user.id)
    return ok(_session_payload(user, await permission_codes(db, user.id), access, refresh, expires_at))


@router.post("/refresh", response_model=ApiResponse[AuthTokens])
async def refresh(data: RefreshRequest, db: DbSession) -> ApiResponse[AuthTokens]:
    user = await db.get(User, decode_token(data.refreshToken, "refresh"))
    if user is None or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user is inactive or missing")
    access, refresh_token, expires_at = issue_tokens(user.id)
    return ok(AuthTokens(accessToken=access, refreshToken=refresh_token, expiresAt=expires_at))


@router.get("/me", response_model=ApiResponse[UserSession])
async def me(user: CurrentUser, db: DbSession) -> ApiResponse[UserSession]:
    return ok(
        UserSession(
            id=user.id,
            name=user.name,
            email=user.email,
            active=user.active,
            permissions=sorted(await permission_codes(db, user.id)),
        )
    )


@router.post("/logout", response_model=ApiResponse[None])
async def logout(_: CurrentUser) -> ApiResponse[None]:
    # Access and refresh tokens are short-lived/self-contained; the client discards them.
    return ok(None)


__all__ = ["router"]

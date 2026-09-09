from __future__ import annotations

from dqh.svc_core.transports.http import ApiResponse, ok
from fastapi import APIRouter

from app.api.deps import DbSession
from app.modules.auth.bearer_auth import CurrentUser
from app.modules.auth.schemas import AuthSession, AuthTokens, LoginRequest, RefreshRequest, UserSession
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse[AuthSession])
async def login(data: LoginRequest, db: DbSession) -> ApiResponse[AuthSession]:
    return ok(await AuthService(db).login(data.email, data.password))


@router.post("/refresh", response_model=ApiResponse[AuthTokens])
async def refresh(data: RefreshRequest, db: DbSession) -> ApiResponse[AuthTokens]:
    return ok(await AuthService(db).refresh(data.refreshToken))


@router.get("/me", response_model=ApiResponse[UserSession])
async def me(user: CurrentUser, db: DbSession) -> ApiResponse[UserSession]:
    return ok(await AuthService(db).session_view(user))


@router.post("/logout", response_model=ApiResponse[None])
async def logout(_: CurrentUser) -> ApiResponse[None]:
    # Access and refresh tokens are short-lived / self-contained; the client discards them.
    return ok(None)


__all__ = ["router"]

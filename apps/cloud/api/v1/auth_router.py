from fastapi import APIRouter, Depends, status

from apps.cloud.api.v1.auth_schemas import LoginIn, RefreshIn, SessionOut, UserOut
from apps.cloud.dependencies import get_auth_service, require_principal
from src.cloud.application.dto.register_request import RegisterRequest
from src.cloud.application.services.auth_service import AuthService
from src.cloud.domain.value_objects.principal import Principal

# Public except /me and /logout; mounted without the global auth dependency.
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    """Open for the first account; afterwards only when CLOUD_ALLOW_REGISTRATION=true. Every account is ADMIN."""
    return await service.register(body)


@router.post("/login", response_model=SessionOut)
async def login(body: LoginIn, service: AuthService = Depends(get_auth_service)):
    return await service.login(body.login, body.password)


@router.post("/refresh", response_model=SessionOut)
async def refresh(body: RefreshIn, service: AuthService = Depends(get_auth_service)):
    """Rotates the pair: the refresh token sent here stops working."""
    return await service.refresh(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_principal)])
async def logout(body: RefreshIn, service: AuthService = Depends(get_auth_service)):
    await service.logout(body.refresh_token)


@router.get("/me", response_model=UserOut)
async def me(principal: Principal = Depends(require_principal), service: AuthService = Depends(get_auth_service)):
    return await service.current_user(principal)

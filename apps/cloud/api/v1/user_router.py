from fastapi import APIRouter, Depends, status

from apps.cloud.api.v1.auth_schemas import UserCreateIn, UserOut, UserUpdateIn
from apps.cloud.dependencies import get_user_service, require_principal
from src.cloud.application.dto.register_request import RegisterRequest
from src.cloud.application.services.user_service import UserService
from src.cloud.domain.value_objects.principal import Principal

# Account administration. No role checks yet: every signed-in account is an ADMIN with full access.
router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(users: UserService = Depends(get_user_service)):
    return await users.list()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreateIn, users: UserService = Depends(get_user_service)):
    request = RegisterRequest(username=body.username, email=body.email, password=body.password,
                              display_name=body.display_name)
    return await users.create(request)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, users: UserService = Depends(get_user_service)):
    return await users.get(user_id)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    body: UserUpdateIn,
    principal: Principal = Depends(require_principal),
    users: UserService = Depends(get_user_service),
):
    acting = principal.subject if principal.is_user else None
    return await users.update(user_id, body.model_dump(exclude_unset=True), acting)

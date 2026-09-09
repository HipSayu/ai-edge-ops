"""User HTTP adapter."""

from __future__ import annotations

from dqh.svc_core.transports.http import ApiResponse, ok
from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession
from app.modules.iam.bearer_auth import require_permission
from app.modules.iam.schemas import UserCreate, UserOut, UserUpdate
from app.modules.iam.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=ApiResponse[list[UserOut]])
async def list_users(
    db: DbSession, _: object = Depends(require_permission("users.read"))
) -> ApiResponse[list[UserOut]]:
    rows = await UserService(db).list_users()
    return ok([UserOut.model_validate(row) for row in rows])


@router.post("", response_model=ApiResponse[UserOut], status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate, db: DbSession, _: object = Depends(require_permission("users.manage"))
) -> ApiResponse[UserOut]:
    return ok(UserOut.model_validate(await UserService(db).create_user(data)))


@router.get("/{user_id}", response_model=ApiResponse[UserOut])
async def get_user(
    user_id: int, db: DbSession, _: object = Depends(require_permission("users.read"))
) -> ApiResponse[UserOut]:
    return ok(UserOut.model_validate(await UserService(db).get_user(user_id)))


@router.patch("/{user_id}", response_model=ApiResponse[UserOut])
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: DbSession,
    _: object = Depends(require_permission("users.manage")),
) -> ApiResponse[UserOut]:
    return ok(UserOut.model_validate(await UserService(db).update_user(user_id, data)))

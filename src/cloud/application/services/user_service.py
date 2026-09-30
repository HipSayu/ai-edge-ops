import uuid
from typing import Any

from src.cloud.application.dto.register_request import RegisterRequest
from src.cloud.application.ports.password_hasher import PasswordHasher
from src.cloud.application.ports.user_repository import UserRepository
from src.cloud.domain.entities.user import User, UserRole, UserStatus
from src.shared.exceptions import AppException, ErrorCode


class UserService:
    """Account administration. No permission model yet: every account is an ADMIN with full access,
    so the only guard is that at least one active account always remains."""

    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def list(self) -> list[User]:
        return await self._users.list()

    async def get(self, user_id: str) -> User:
        user = await self._users.get(user_id)
        if user is None:
            raise AppException(ErrorCode.NOT_FOUND, f"User {user_id} not found")
        return user

    async def create(self, request: RegisterRequest) -> User:
        return await self._users.add(
            User(
                id=str(uuid.uuid4()), username=request.username, email=request.email.lower(),
                password_hash=self._hasher.hash(request.password), display_name=request.display_name,
                role=UserRole.ADMIN,
            )
        )

    async def update(self, user_id: str, changes: dict[str, Any], acting_user_id: str | None) -> User:
        user = await self.get(user_id)
        if "status" in changes and changes["status"] != UserStatus.ACTIVE:
            if user_id == acting_user_id:
                raise AppException(ErrorCode.CONFLICT, "You cannot disable your own account")
            if user.status == UserStatus.ACTIVE and await self._active_accounts() <= 1:
                raise AppException(ErrorCode.CONFLICT, "Cannot disable the last active account")
            user.status = UserStatus(changes["status"])
        elif "status" in changes:
            user.status = UserStatus.ACTIVE
        if "display_name" in changes:
            user.display_name = changes["display_name"]
        if changes.get("password"):
            user.password_hash = self._hasher.hash(changes["password"])
        return await self._users.save(user)

    async def _active_accounts(self) -> int:
        return sum(1 for u in await self._users.list() if u.status == UserStatus.ACTIVE)

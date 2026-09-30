from typing import Protocol

from src.cloud.domain.entities.user import User


class UserRepository(Protocol):
    async def add(self, user: User) -> User:
        """Raises AppException(CONFLICT) when the username or email is taken."""
        ...

    async def get(self, user_id: str) -> User | None: ...

    async def get_by_login(self, login: str) -> User | None:
        """Looks a user up by email or username (case-insensitive)."""
        ...

    async def count(self) -> int: ...

    async def list(self) -> list[User]: ...

    async def save(self, user: User) -> User:
        """Persists display_name, role, status and password_hash."""
        ...

    async def touch_login(self, user_id: str) -> None:
        """Records a successful sign-in (last_login_at)."""
        ...

from src.cloud.domain.entities.user import User
from src.shared.domain.clock import Clock
from src.shared.exceptions import AppException, ErrorCode


class FakeUserRepository:
    def __init__(self) -> None:
        self._items: dict[str, User] = {}

    async def add(self, user: User) -> User:
        if any(u.email.lower() == user.email.lower() or u.username.lower() == user.username.lower()
               for u in self._items.values()):
            raise AppException(ErrorCode.CONFLICT, "Username or email already registered")
        user.created_at = user.updated_at = Clock.now()
        self._items[user.id] = user
        return user

    async def get(self, user_id: str) -> User | None:
        return self._items.get(user_id)

    async def get_by_login(self, login: str) -> User | None:
        login = login.lower()
        return next((u for u in self._items.values() if login in (u.email.lower(), u.username.lower())), None)

    async def count(self) -> int:
        return len(self._items)

    async def list(self) -> list[User]:
        return list(self._items.values())

    async def save(self, user: User) -> User:
        user.updated_at = Clock.now()
        self._items[user.id] = user
        return user

    async def touch_login(self, user_id: str) -> None:
        self._items[user_id].last_login_at = Clock.now()

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


@dataclass(slots=True)
class User:
    id: str
    username: str
    email: str
    password_hash: str | None = None
    display_name: str | None = None
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login_at: datetime | None = None

    def __post_init__(self) -> None:
        # Rows come back with plain strings for the Postgres enums
        self.role = UserRole(self.role)
        self.status = UserStatus(self.status)

    def can_sign_in(self) -> bool:
        return self.status == UserStatus.ACTIVE and self.password_hash is not None

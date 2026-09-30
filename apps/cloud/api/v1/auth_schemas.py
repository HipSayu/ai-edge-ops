"""Auth request/response models. camelCase on the wire to match the dashboard's AuthTokens."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.cloud.domain.entities.user import UserRole, UserStatus


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class LoginIn(_Camel):
    login: str = Field(min_length=1, max_length=255, description="Email or username")
    password: str = Field(min_length=1, max_length=128)


class RefreshIn(_Camel):
    refresh_token: str = Field(min_length=1)


class UserOut(_Camel):
    id: str
    username: str
    email: str
    display_name: str | None
    role: UserRole
    status: UserStatus
    created_at: datetime | None
    last_login_at: datetime | None


class UserCreateIn(_Camel):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=255)


class UserUpdateIn(_Camel):
    """Only the fields sent are changed. Roles are not editable yet (everyone is ADMIN)."""

    display_name: str | None = Field(default=None, max_length=255)
    status: UserStatus | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class SessionOut(_Camel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")
    user: UserOut

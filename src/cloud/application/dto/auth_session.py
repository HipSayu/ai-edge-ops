from dataclasses import dataclass

from src.cloud.domain.entities.user import User


@dataclass(frozen=True)
class AuthSession:
    """Result of login/register/refresh: a token pair plus the signed-in user."""

    access_token: str
    refresh_token: str
    expires_in: int
    user: User

from dataclasses import dataclass
from enum import StrEnum

from src.cloud.domain.entities.user import UserRole


class PrincipalKind(StrEnum):
    USER = "user"  # a person, authenticated with a JWT access token
    SERVICE = "service"  # a machine client (assistant, scripts), authenticated with a static API key


@dataclass(frozen=True)
class Principal:
    """Who is calling. Every authenticated request carries one."""

    kind: PrincipalKind
    subject: str  # user id, or "service"
    role: UserRole

    @property
    def is_user(self) -> bool:
        return self.kind == PrincipalKind.USER

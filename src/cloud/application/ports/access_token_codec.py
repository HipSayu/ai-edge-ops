from typing import Protocol

from src.cloud.domain.value_objects.principal import Principal


class AccessTokenCodec(Protocol):
    """Short-lived, self-contained access tokens (JWT today)."""

    @property
    def ttl_sec(self) -> int: ...

    def encode(self, principal: Principal) -> str: ...

    def decode(self, token: str) -> Principal | None:
        """None for malformed, forged or expired tokens."""
        ...

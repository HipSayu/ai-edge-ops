from typing import Protocol


class RefreshTokenStore(Protocol):
    """Opaque, revocable refresh tokens. Implementations store only a hash of the token."""

    async def issue(self, user_id: str) -> str:
        """Creates a new refresh token for the user and returns it (plaintext, shown once)."""
        ...

    async def consume(self, token: str) -> str | None:
        """Atomically invalidates the token and returns its user id; None if unknown or expired."""
        ...

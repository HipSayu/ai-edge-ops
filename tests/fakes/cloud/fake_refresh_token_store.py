import secrets


class FakeRefreshTokenStore:
    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}

    async def issue(self, user_id: str) -> str:
        token = secrets.token_urlsafe(16)
        self._tokens[token] = user_id
        return token

    async def consume(self, token: str) -> str | None:
        return self._tokens.pop(token, None)

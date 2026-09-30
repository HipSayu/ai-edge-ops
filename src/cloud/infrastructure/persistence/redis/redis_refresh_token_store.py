import hashlib
import secrets

from redis.asyncio import Redis


class RedisRefreshTokenStore:
    """`auth:refresh:{sha256(token)}` -> user id, expiring after `ttl_sec`. GETDEL makes each token single-use."""

    def __init__(self, redis: Redis, ttl_sec: int, prefix: str = "auth:refresh") -> None:
        self._redis = redis
        self._ttl_sec = ttl_sec
        self._prefix = prefix

    async def issue(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        await self._redis.set(self._key(token), user_id, ex=self._ttl_sec)
        return token

    async def consume(self, token: str) -> str | None:
        value = await self._redis.getdel(self._key(token))
        if value is None:
            return None
        return value.decode() if isinstance(value, bytes) else value

    def _key(self, token: str) -> str:
        return f"{self._prefix}:{hashlib.sha256(token.encode('utf-8')).hexdigest()}"

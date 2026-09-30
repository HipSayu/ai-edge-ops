import json
from typing import Any

from redis.asyncio import Redis


class RedisTelemetryRepository:
    """`telemetry:{node}:latest` hash + `telemetry:{node}:{kind}` capped list per kind."""

    def __init__(self, redis: Redis, history_size: int = 720, ttl_sec: int = 3600) -> None:
        self._redis = redis
        self._history_size = history_size
        self._ttl = ttl_sec

    async def record(self, node_id: str, kind: str, key: str, sample: dict[str, Any]) -> None:
        body = json.dumps(sample)
        latest_key = f"telemetry:{node_id}:latest"
        history_key = f"telemetry:{node_id}:{kind}"
        async with self._redis.pipeline(transaction=False) as pipe:
            pipe.hset(latest_key, key, body)
            pipe.expire(latest_key, self._ttl)
            pipe.lpush(history_key, body)
            pipe.ltrim(history_key, 0, self._history_size - 1)
            pipe.expire(history_key, self._ttl)
            await pipe.execute()

    async def latest(self, node_id: str) -> dict[str, dict[str, Any]]:
        raw = await self._redis.hgetall(f"telemetry:{node_id}:latest")
        return {self._s(k): json.loads(v) for k, v in raw.items()}

    async def history(self, node_id: str, kind: str, limit: int = 100) -> list[dict[str, Any]]:
        raw = await self._redis.lrange(f"telemetry:{node_id}:{kind}", 0, limit - 1)
        return [json.loads(v) for v in raw]

    async def ping(self) -> bool:
        return bool(await self._redis.ping())

    @staticmethod
    def _s(value: bytes | str) -> str:
        return value.decode() if isinstance(value, bytes) else value

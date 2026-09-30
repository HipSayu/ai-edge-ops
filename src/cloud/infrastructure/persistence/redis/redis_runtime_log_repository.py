import json
from typing import Any

from redis.asyncio import Redis

from src.shared.contracts import RuntimeLogBatch


class RedisRuntimeLogRepository:
    """`logs:runtime:{id}` capped list, newest first; expires when a runtime stops logging."""

    def __init__(self, redis: Redis, max_lines: int = 2000, ttl_sec: int = 86400) -> None:
        self._redis = redis
        self._max_lines = max_lines
        self._ttl = ttl_sec

    async def append(self, batch: RuntimeLogBatch) -> None:
        if not batch.lines:
            return
        key = self._key(batch.runtime_id)
        entries = [
            json.dumps({"node_id": batch.node_id, "runtime_id": batch.runtime_id, "runtime_name": batch.runtime_name,
                        **line.model_dump(mode="json")})
            for line in batch.lines
        ]
        async with self._redis.pipeline(transaction=False) as pipe:
            pipe.lpush(key, *entries)
            pipe.ltrim(key, 0, self._max_lines - 1)
            pipe.expire(key, self._ttl)
            await pipe.execute()

    async def recent(self, runtime_id: str, limit: int = 200) -> list[dict[str, Any]]:
        raw = await self._redis.lrange(self._key(runtime_id), 0, limit - 1)
        return [json.loads(v) for v in reversed(raw)]

    @staticmethod
    def _key(runtime_id: str) -> str:
        return f"logs:runtime:{runtime_id}"

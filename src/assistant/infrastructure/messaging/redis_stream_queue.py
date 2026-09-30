from collections.abc import AsyncIterator

from redis.asyncio import Redis

_FRAME = "frame"
_END = "end"


class RedisStreamQueue:
    """Chat streams on Redis Streams, so POST /chat/stream and GET /chat/stream/{id} may hit different replicas.

    `chat:stream:{id}` holds the frames; `chat:stream:{id}:open` exists until one consumer claims the stream.
    Both expire after `ttl_sec`, so abandoned streams clean themselves up.
    """

    def __init__(
        self, redis: Redis, ttl_sec: float = 600.0, idle_timeout_sec: float = 120.0, prefix: str = "chat:stream"
    ) -> None:
        self._redis = redis
        self._ttl = max(1, int(ttl_sec))
        # Longer than the slowest tool call, which emits no frames while it runs
        self._block_ms = int(idle_timeout_sec * 1000)
        self._prefix = prefix

    async def open(self, stream_id: str) -> None:
        await self._redis.set(self._claim_key(stream_id), "1", ex=self._ttl)

    async def put(self, stream_id: str, frame: str) -> None:
        await self._append(stream_id, {_FRAME: frame})

    async def close(self, stream_id: str) -> None:
        await self._append(stream_id, {_END: "1"})

    async def subscribe(self, stream_id: str) -> AsyncIterator[str] | None:
        claimed = await self._redis.delete(self._claim_key(stream_id))
        return self._drain(stream_id) if claimed else None

    async def ping(self) -> bool:
        return bool(await self._redis.ping())

    async def _append(self, stream_id: str, fields: dict[str, str]) -> None:
        key = self._key(stream_id)
        async with self._redis.pipeline(transaction=False) as pipe:
            pipe.xadd(key, fields)
            pipe.expire(key, self._ttl)
            await pipe.execute()

    async def _drain(self, stream_id: str) -> AsyncIterator[str]:
        key, last_id = self._key(stream_id), "0"
        try:
            while True:
                batches = await self._redis.xread({key: last_id}, block=self._block_ms)
                if not batches:
                    return  # producer went silent too long: give up rather than hang the SSE response
                for entry_id, fields in batches[0][1]:
                    last_id = entry_id
                    fields = {self._text(k): self._text(v) for k, v in fields.items()}
                    if _END in fields:
                        return
                    yield fields[_FRAME]
        finally:
            await self._redis.delete(key)

    def _key(self, stream_id: str) -> str:
        return f"{self._prefix}:{stream_id}"

    def _claim_key(self, stream_id: str) -> str:
        return f"{self._key(stream_id)}:open"

    @staticmethod
    def _text(value: bytes | str) -> str:
        return value.decode() if isinstance(value, bytes) else value

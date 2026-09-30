import json

import asyncpg


class PostgresDatabase:
    """asyncpg pool with JSON/JSONB codecs registered."""

    def __init__(self, dsn: str, min_size: int = 1, max_size: int = 10) -> None:
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._pool: asyncpg.Pool | None = None

    @staticmethod
    async def _init_connection(conn: asyncpg.Connection) -> None:
        for type_name in ("json", "jsonb"):
            await conn.set_type_codec(type_name, encoder=json.dumps, decoder=json.loads, schema="pg_catalog")

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(
            self._dsn, min_size=self._min_size, max_size=self._max_size, init=self._init_connection
        )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("PostgresDatabase is not connected")
        return self._pool

    async def ping(self) -> bool:
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT 1") == 1

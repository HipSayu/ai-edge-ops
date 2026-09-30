from __future__ import annotations

from typing import Any, Generic, TypeVar

from src.cloud.infrastructure.persistence.postgres.postgres_database import PostgresDatabase
from src.cloud.infrastructure.persistence.postgres.row_mapper import RowMapper

T = TypeVar("T")


class PostgresRepository(Generic[T]):
    """Base for repositories whose queries return rows of one entity type."""

    entity: type[T]

    def __init__(self, db: PostgresDatabase) -> None:
        self._db = db

    async def _one(self, sql: str, *args: Any) -> T | None:
        row = await self._db.pool.fetchrow(sql, *args)
        return RowMapper.to(self.entity, row) if row else None

    async def _many(self, sql: str, *args: Any) -> list[T]:
        return [RowMapper.to(self.entity, r) for r in await self._db.pool.fetch(sql, *args)]

    async def _execute(self, sql: str, *args: Any) -> None:
        await self._db.pool.execute(sql, *args)

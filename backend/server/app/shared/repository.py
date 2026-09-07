"""Generic async repository. Subclass per aggregate root and add query methods.

Repositories own *all* query construction and ``flush`` rows, but never ``commit`` —
the transaction boundary belongs to the service.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from dqh.svc_core.transports.http import PaginationParams as PageParams
from sqlalchemy import ColumnExpressionArgument, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, entity_id: int) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)
        await self.session.flush()

    def _select(self, *where: ColumnExpressionArgument[bool]) -> Select[tuple[ModelT]]:
        stmt: Select[tuple[ModelT]] = select(self.model)
        for clause in where:
            stmt = stmt.where(clause)
        return stmt

    async def list(
        self,
        *where: ColumnExpressionArgument[bool],
        order_by: Any | None = None,
        params: PageParams | None = None,
    ) -> list[ModelT]:
        stmt = self._select(*where)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        if params is not None:
            stmt = stmt.limit(params.limit).offset(params.offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *where: ColumnExpressionArgument[bool]) -> int:
        stmt = select(func.count()).select_from(self.model)
        for clause in where:
            stmt = stmt.where(clause)
        return int((await self.session.execute(stmt)).scalar_one())

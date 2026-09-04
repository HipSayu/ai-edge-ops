"""Observability data access."""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.http import PaginationParams as PageParams
from sqlalchemy import cast, func, select
from sqlalchemy.types import Date

from app.modules.observability.domain import AlertStatus, AlertType
from app.modules.observability.models import Alert, Violation
from app.shared.repository import BaseRepository


class ViolationRepository(BaseRepository[Violation]):
    model = Violation

    async def list_page(
        self,
        *,
        device_id: int | None,
        violation_type: str | None,
        since: dt.datetime | None,
        params: PageParams,
    ) -> tuple[list[Violation], int]:
        clauses = []
        if device_id is not None:
            clauses.append(Violation.device_id == device_id)
        if violation_type:
            clauses.append(Violation.violation_type == violation_type)
        if since:
            clauses.append(Violation.recorded_at >= since)
        items = await self.list(*clauses, order_by=Violation.recorded_at.desc(), params=params)
        total = await self.count(*clauses)
        return items, total

    async def count_since(self, since: dt.datetime) -> int:
        return await self.count(Violation.recorded_at >= since)

    async def count_by_type(self, since: dt.datetime | None) -> list[tuple[str, int]]:
        stmt = select(Violation.violation_type, func.count()).group_by(Violation.violation_type)
        if since:
            stmt = stmt.where(Violation.recorded_at >= since)
        return list((await self.session.execute(stmt)).all())

    async def daily_counts(self, since: dt.datetime) -> list[tuple[dt.date, int]]:
        day = cast(Violation.recorded_at, Date)
        stmt = (
            select(day, func.count())
            .where(Violation.recorded_at >= since)
            .group_by(day)
            .order_by(day)
        )
        return list((await self.session.execute(stmt)).all())


class AlertRepository(BaseRepository[Alert]):
    model = Alert

    async def list_page(
        self,
        *,
        status: AlertStatus | None,
        alert_type: AlertType | None,
        device_id: int | None,
        params: PageParams,
    ) -> tuple[list[Alert], int]:
        clauses = []
        if status is not None:
            clauses.append(Alert.status == status)
        if alert_type is not None:
            clauses.append(Alert.type == alert_type)
        if device_id is not None:
            clauses.append(Alert.device_id == device_id)
        items = await self.list(*clauses, order_by=Alert.created_at.desc(), params=params)
        total = await self.count(*clauses)
        return items, total

    async def find_open(self, alert_type: AlertType, device_id: int | None) -> Alert | None:
        stmt = select(Alert).where(
            Alert.type == alert_type,
            Alert.status != AlertStatus.RESOLVED,
            Alert.device_id.is_(device_id) if device_id is None else Alert.device_id == device_id,
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def count_open(self) -> int:
        return await self.count(Alert.status != AlertStatus.RESOLVED)

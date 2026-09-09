"""Agent data access."""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.persistence.sqlalchemy import BaseRepository
from dqh.svc_core.transports.http import PaginationParams as PageParams
from sqlalchemy import func, select

from app.modules.agent.models import Device, MetricSample
from app.modules.agent.rules import DeviceStatus


class DeviceRepository(BaseRepository[Device]):
    model = Device

    async def get_by_name(self, name: str) -> Device | None:
        stmt = select(Device).where(Device.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    def _filters(self, site: str | None, status: DeviceStatus | None) -> list:
        clauses = []
        if site:
            clauses.append(Device.site == site)
        if status:
            clauses.append(Device.status == status)
        return clauses

    async def list_page(
        self, *, site: str | None, status: DeviceStatus | None, params: PageParams
    ) -> tuple[list[Device], int]:
        clauses = self._filters(site, status)
        return await self.page(*clauses, order_by=Device.name, params=params)

    async def count_by_status(self) -> dict[DeviceStatus, int]:
        stmt = select(Device.status, func.count()).group_by(Device.status)
        rows = (await self.session.execute(stmt)).all()
        return {status: count for status, count in rows}

    async def list_stale(self, cutoff: dt.datetime) -> list[Device]:
        stmt = select(Device).where(
            Device.status != DeviceStatus.OFFLINE,
            Device.last_seen_at.is_not(None),
            Device.last_seen_at < cutoff,
        )
        return list((await self.session.execute(stmt)).scalars().all())


class MetricSampleRepository(BaseRepository[MetricSample]):
    model = MetricSample

    async def list_for_device(
        self, device_id: int, *, since: dt.datetime | None, params: PageParams
    ) -> tuple[list[MetricSample], int]:
        clauses = [MetricSample.device_id == device_id]
        if since:
            clauses.append(MetricSample.recorded_at >= since)
        return await self.page(*clauses, order_by=MetricSample.recorded_at.desc(), params=params)

    async def avg_latency_since(self, since: dt.datetime) -> float | None:
        stmt = select(func.avg(MetricSample.inference_latency_ms)).where(
            MetricSample.recorded_at >= since
        )
        value = (await self.session.execute(stmt)).scalar_one_or_none()
        return float(value) if value is not None else None

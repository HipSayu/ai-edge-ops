"""Agent data access — Device is the desired-config table now."""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.persistence.sqlalchemy import BaseRepository
from dqh.svc_core.transports.http import PaginationParams as PageParams
from sqlalchemy import func, select

from app.modules.agent.models import Device, MetricSample


class DeviceRepository(BaseRepository[Device]):
    model = Device

    async def get_by_name(self, name: str) -> Device | None:
        return (
            await self.session.execute(select(Device).where(Device.name == name))
        ).scalar_one_or_none()

    async def list_all(self, *, site: str | None) -> list[Device]:
        stmt = select(Device).order_by(Device.name)
        if site:
            stmt = stmt.where(Device.site == site)
        return list((await self.session.execute(stmt)).scalars().all())


class MetricSampleRepository(BaseRepository[MetricSample]):
    model = MetricSample

    async def list_for_device(
        self, device_id: str, *, since: dt.datetime | None, params: PageParams
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

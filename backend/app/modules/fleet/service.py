"""Fleet use-cases. No FastAPI here — safe to call from workers, CLI, LLM tools."""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.errors import ConflictError, NotFoundError
from dqh.svc_core.http import Page
from dqh.svc_core.http import PaginationParams as PageParams
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.events import event_bus
from app.modules.fleet.domain import (
    DeviceLatencyDegraded,
    DeviceRegistered,
    DeviceStatus,
    DeviceWentOffline,
    evaluate_status,
)
from app.modules.fleet.models import Device, MetricSample
from app.modules.fleet.repository import DeviceRepository, MetricSampleRepository
from app.modules.fleet.schemas import DeviceCreate, DeviceUpdate, FleetHealth, HeartbeatIn


def _utcnow() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)


class FleetService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.devices = DeviceRepository(session)
        self.metrics = MetricSampleRepository(session)

    # --- devices -------------------------------------------------------------
    async def register_device(self, data: DeviceCreate) -> Device:
        if await self.devices.get_by_name(data.name):
            raise ConflictError(f"device '{data.name}' already exists")
        device = Device(**data.model_dump())
        await self.devices.add(device)
        await self.session.commit()
        await event_bus.publish(DeviceRegistered(device_id=device.id, name=device.name))
        return device

    async def get_device(self, device_id: int) -> Device:
        device = await self.devices.get(device_id)
        if device is None:
            raise NotFoundError(f"device {device_id} not found")
        return device

    async def list_devices(
        self, *, site: str | None, status: DeviceStatus | None, params: PageParams
    ) -> Page[Device]:
        items, total = await self.devices.list_page(site=site, status=status, params=params)
        return Page.of(items, total=total, params=params)

    async def update_device(self, device_id: int, data: DeviceUpdate) -> Device:
        device = await self.get_device(device_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(device, field, value)
        await self.session.commit()
        return device

    async def delete_device(self, device_id: int) -> None:
        device = await self.get_device(device_id)
        await self.devices.delete(device)
        await self.session.commit()

    # --- monitoring --------------------------------------------------------
    async def record_heartbeat(self, device_id: int, hb: HeartbeatIn) -> tuple[Device, MetricSample]:
        device = await self.get_device(device_id)
        now = _utcnow()
        recorded_at = hb.recorded_at or now
        sample = MetricSample(
            device_id=device_id,
            recorded_at=recorded_at,
            **hb.model_dump(exclude={"recorded_at"}),
        )
        await self.metrics.add(sample)

        previous = device.status
        device.last_seen_at = recorded_at
        device.status = evaluate_status(
            last_seen_at=recorded_at,
            now=now,
            offline_threshold_seconds=settings.offline_threshold_seconds,
            inference_latency_ms=hb.inference_latency_ms,
            latency_slo_ms=settings.latency_slo_ms,
        )
        await self.session.commit()

        if device.status is DeviceStatus.DEGRADED and previous is not DeviceStatus.DEGRADED:
            await event_bus.publish(
                DeviceLatencyDegraded(
                    device_id=device_id,
                    inference_latency_ms=hb.inference_latency_ms or 0.0,
                    slo_ms=settings.latency_slo_ms,
                )
            )
        return device, sample

    async def list_metrics(
        self, device_id: int, *, since: dt.datetime | None, params: PageParams
    ) -> Page[MetricSample]:
        await self.get_device(device_id)
        items, total = await self.metrics.list_for_device(device_id, since=since, params=params)
        return Page.of(items, total=total, params=params)

    async def sweep_offline(self) -> int:
        """Mark devices with a stale heartbeat OFFLINE. Intended for a scheduler."""
        cutoff = _utcnow() - dt.timedelta(seconds=settings.offline_threshold_seconds)
        stale = await self.devices.list_stale(cutoff)
        for device in stale:
            device.status = DeviceStatus.OFFLINE
        await self.session.commit()
        for device in stale:
            await event_bus.publish(
                DeviceWentOffline(device_id=device.id, last_seen_at=device.last_seen_at)
            )
        return len(stale)

    # --- read models for other modules -----------------------------------
    async def fleet_health(self) -> FleetHealth:
        counts = await self.devices.count_by_status()
        return FleetHealth(
            total=sum(counts.values()),
            online=counts.get(DeviceStatus.ONLINE, 0),
            degraded=counts.get(DeviceStatus.DEGRADED, 0),
            offline=counts.get(DeviceStatus.OFFLINE, 0),
            provisioning=counts.get(DeviceStatus.PROVISIONING, 0),
        )

    async def avg_inference_latency_ms(self, since: dt.datetime) -> float | None:
        return await self.metrics.avg_latency_since(since)

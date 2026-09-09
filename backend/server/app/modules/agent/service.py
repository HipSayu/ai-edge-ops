"""Agent use-cases. No FastAPI here - safe to call from workers, CLI, LLM tools."""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.contracts.errors import ConflictError, NotFoundError
from dqh.svc_core.helpers.time import utcnow
from dqh.svc_core.transports.http import Page
from dqh.svc_core.transports.http import PaginationParams as PageParams
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.events import event_bus
from app.modules.agent.event import (
    DeviceLatencyDegraded,
    DeviceRegistered,
    DeviceWentOffline,
    HeartbeatRecorded,
)
from app.modules.agent.models import Device, MetricSample
from app.modules.agent.repository import DeviceRepository, MetricSampleRepository
from app.modules.agent.rules import DeviceStatus, evaluate_status
from app.modules.agent.schemas import AgentHealth, DeviceCreate, DeviceUpdate, HeartbeatIn


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.devices = DeviceRepository(session)
        self.metrics = MetricSampleRepository(session)

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

    async def record_heartbeat(self, device_id: int, hb: HeartbeatIn) -> tuple[Device, MetricSample]:
        device = await self.get_device(device_id)
        now = utcnow()
        recorded_at = hb.recorded_at or now
        _DEVICE_FIELDS = {"agent_version", "ip_address", "uptime_s", "active_model_version_id"}
        sample = MetricSample(
            device_id=device_id,
            recorded_at=recorded_at,
            **hb.model_dump(exclude={"recorded_at", *_DEVICE_FIELDS}),
        )
        await self.metrics.add(sample)

        previous = device.status
        device.last_seen_at = recorded_at
        for field in _DEVICE_FIELDS:
            if (value := getattr(hb, field)) is not None:
                setattr(device, field, value)
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
        await event_bus.publish(
            HeartbeatRecorded(
                device_id=device_id,
                recorded_at=recorded_at,
                cpu_percent=hb.cpu_percent,
                gpu_percent=hb.gpu_percent,
                mem_percent=hb.mem_percent,
                mem_used_mb=hb.mem_used_mb,
                mem_total_mb=hb.mem_total_mb,
                disk_percent=hb.disk_percent,
                temperature_c=hb.temperature_c,
                fps=hb.fps,
                inference_latency_ms=hb.inference_latency_ms,
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
        cutoff = utcnow() - dt.timedelta(seconds=settings.offline_threshold_seconds)
        stale = await self.devices.list_stale(cutoff)
        for device in stale:
            device.status = DeviceStatus.OFFLINE
        await self.session.commit()
        for device in stale:
            await event_bus.publish(
                DeviceWentOffline(device_id=device.id, last_seen_at=device.last_seen_at)
            )
        return len(stale)

    async def agent_health(self) -> AgentHealth:
        counts = await self.devices.count_by_status()
        return AgentHealth(
            total=sum(counts.values()),
            online=counts.get(DeviceStatus.ONLINE, 0),
            degraded=counts.get(DeviceStatus.DEGRADED, 0),
            offline=counts.get(DeviceStatus.OFFLINE, 0),
            provisioning=counts.get(DeviceStatus.PROVISIONING, 0),
        )

    async def avg_inference_latency_ms(self, since: dt.datetime) -> float | None:
        return await self.metrics.avg_latency_since(since)
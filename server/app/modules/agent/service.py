"""Agent use-cases. No FastAPI here - safe to call from workers, CLI, LLM tools.

``Device`` is the desired config (Postgres). The reported runtime is merged in
from :data:`app.core.fleet.fleet` (in-memory).
"""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.contracts.errors import ConflictError, NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.events import event_bus
from app.core.fleet import fleet
from app.modules.agent.event import (
    DeviceConfigChanged,
    DeviceLatencyDegraded,
    DeviceRegistered,
    HeartbeatRecorded,
)
from app.modules.agent.models import Device
from app.modules.agent.repository import DeviceRepository
from app.modules.agent.rules import DeviceStatus
from app.modules.agent.schemas import AgentHealth, DeviceCreate, DeviceOut, DeviceUpdate, HeartbeatIn


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.devices = DeviceRepository(session)

    # --- desired config ------------------------------------------------------
    async def register_device(self, data: DeviceCreate) -> DeviceOut:
        if await self.devices.get(data.device_id):
            raise ConflictError(f"device '{data.device_id}' already exists")
        if await self.devices.get_by_name(data.name):
            raise ConflictError(f"device name '{data.name}' is taken")
        device = Device(**data.model_dump())
        await self.devices.add(device)
        await self.session.commit()
        await event_bus.publish(DeviceRegistered(device_id=device.device_id, name=device.name))
        return self._view(device)

    async def get_device(self, device_id: str) -> Device:
        device = await self.devices.get(device_id)
        if device is None:
            raise NotFoundError(f"device {device_id} not found")
        return device

    async def get_device_view(self, device_id: str) -> DeviceOut:
        if (device := await self.devices.get(device_id)) is not None:
            return self._view(device)
        if fleet.get(device_id) is not None:  # seen over MQTT, no config row
            return self._view(None, device_id=device_id)
        raise NotFoundError(f"device {device_id} not found")

    async def list_devices(self, *, site: str | None) -> list[DeviceOut]:
        rows = {d.device_id: d for d in await self.devices.list_all(site=site)}
        seen = set(fleet.all())
        views = [self._view(rows[i]) for i in rows]
        if site is None:
            views += [self._view(None, device_id=i) for i in seen - rows.keys()]
        return sorted(views, key=lambda v: v.name)

    async def update_device(self, device_id: str, data: DeviceUpdate) -> DeviceOut:
        device = await self.get_device(device_id)
        changed = data.model_dump(exclude_unset=True)
        for field, value in changed.items():
            setattr(device, field, value)
        await self.session.commit()
        if {"inference", "cameras", "agent_config"} & changed.keys():
            await event_bus.publish(DeviceConfigChanged(device_id=device_id))
        return self._view(device)

    async def delete_device(self, device_id: str) -> None:
        device = await self.get_device(device_id)
        await self.devices.delete(device)
        await self.session.commit()
        fleet.forget(device_id)

    # --- reported runtime --------------------------------------------------
    async def record_heartbeat(self, device_id: str, hb: HeartbeatIn) -> tuple[DeviceOut, dict]:
        recorded_at = hb.recorded_at or dt.datetime.now(dt.timezone.utc)
        transition = fleet.record_heartbeat(device_id, hb)
        status = fleet.get(device_id).status()

        if status is DeviceStatus.DEGRADED and (transition is None or transition.old is not DeviceStatus.DEGRADED):
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
        device = await self.devices.get(device_id)
        return self._view(device, device_id=device_id), fleet.recent_samples(device_id, limit=1)[-1]

    def list_metrics(self, device_id: str, *, since: dt.datetime | None, limit: int = 900) -> list[dict]:
        return fleet.recent_samples(device_id, since=since, limit=limit)

    async def agent_health(self) -> AgentHealth:
        """Counts over the union of known (config) + seen (fleet) devices."""
        counts: dict[DeviceStatus, int] = {}
        for view in await self.list_devices(site=None):
            counts[view.status] = counts.get(view.status, 0) + 1
        return AgentHealth(
            total=sum(counts.values()),
            online=counts.get(DeviceStatus.ONLINE, 0),
            degraded=counts.get(DeviceStatus.DEGRADED, 0),
            offline=counts.get(DeviceStatus.OFFLINE, 0),
            provisioning=counts.get(DeviceStatus.PROVISIONING, 0),
        )

    def avg_inference_latency_ms(self, since: dt.datetime) -> float | None:
        return fleet.avg_latency(since)

    # --- merge -----------------------------------------------------------
    @staticmethod
    def _view(device: Device | None, *, device_id: str | None = None) -> DeviceOut:
        did = device.device_id if device else device_id
        rs = fleet.get(did)
        base = dict(
            device_id=did,
            name=device.name if device else did,
            site=device.site if device else "unassigned",
            labels=device.labels if device else {},
            desired_image=device.desired_image if device else None,
            cameras=device.cameras if device else [],
            inference=device.inference if device else {},
            agent_config=device.agent_config if device else {},
            known=device is not None,
        )
        if rs is None:
            return DeviceOut(status=DeviceStatus.PROVISIONING, **base)
        return DeviceOut(
            status=rs.status(),
            last_seen_at=rs.last_seen_at,
            agent_version=rs.agent_version,
            ip_address=rs.ip_address,
            uptime_s=rs.uptime_s,
            backend=rs.backend,
            arch=rs.arch,
            active_image=rs.active_image,
            runtime_status=rs.runtime_status,
            in_sync=bool(base["desired_image"]) and rs.active_image == base["desired_image"],
            **base,
        )

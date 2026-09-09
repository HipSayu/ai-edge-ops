"""Fleet tools — edge devices and their health."""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.transports.http import PaginationParams

from app.mcp._session import session_scope
from app.modules.agent import AgentService
from app.modules.agent.rules import DeviceStatus


async def list_devices(site: str | None = None, status: str | None = None, limit: int = 50) -> dict:
    """List edge devices, optionally filtered by site or status
    (provisioning|online|degraded|offline). Returns id, name, site, status,
    last_seen_at, agent_version, active_image."""
    st = DeviceStatus(status) if status else None
    async with session_scope() as session:
        page = await AgentService(session).list_devices(
            site=site, status=st, params=PaginationParams(page=1, page_size=min(limit, 200))
        )
        return {
            "total": page.total,
            "devices": [
                {
                    "id": d.id,
                    "name": d.name,
                    "site": d.site,
                    "status": str(d.status),
                    "backend": d.backend,
                    "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
                    "agent_version": d.agent_version,
                    "active_image": d.active_image,
                }
                for d in page.items
            ],
        }


async def get_device(device_id: int) -> dict:
    """Full detail for one device by id."""
    async with session_scope() as session:
        d = await AgentService(session).get_device(device_id)
        return {
            "id": d.id,
            "name": d.name,
            "site": d.site,
            "hardware": d.hardware,
            "status": str(d.status),
            "backend": d.backend,
            "arch": d.arch,
            "ip_address": d.ip_address,
            "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
            "agent_version": d.agent_version,
            "uptime_s": d.uptime_s,
            "active_image": d.active_image,
            "labels": d.labels,
        }


async def fleet_health() -> dict:
    """Device counts by status and the 24h average inference latency (ms)."""
    async with session_scope() as session:
        svc = AgentService(session)
        health = await svc.agent_health()
        day_ago = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)
        latency = await svc.avg_inference_latency_ms(day_ago)
        return {
            "total": health.total,
            "online": health.online,
            "degraded": health.degraded,
            "offline": health.offline,
            "provisioning": health.provisioning,
            "avg_inference_latency_ms_24h": latency,
        }


async def device_metrics(device_id: int, hours: int = 6, limit: int = 100) -> dict:
    """Recent telemetry samples for a device (cpu/gpu/mem/fps/latency)."""
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    async with session_scope() as session:
        page = await AgentService(session).list_metrics(
            device_id, since=since, params=PaginationParams(page=1, page_size=min(limit, 500))
        )
        return {
            "device_id": device_id,
            "samples": [
                {
                    "recorded_at": m.recorded_at.isoformat(),
                    "cpu_percent": m.cpu_percent,
                    "gpu_percent": m.gpu_percent,
                    "mem_percent": m.mem_percent,
                    "fps": m.fps,
                    "inference_latency_ms": m.inference_latency_ms,
                }
                for m in page.items
            ],
        }


TOOLS = [list_devices, get_device, fleet_health, device_metrics]

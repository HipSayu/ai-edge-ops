"""Fleet tools — edge devices and their health."""

from __future__ import annotations

import datetime as dt

from app.core.database import session_scope
from app.modules.agent import AgentService


async def list_devices(site: str | None = None, limit: int = 50) -> dict:
    """List edge devices - merged desired config + reported runtime. Fields:
    device_id, name, site, status, known, last_seen_at, agent_version,
    active_image, desired_image, in_sync."""
    async with session_scope() as session:
        devices = await AgentService(session).list_devices(site=site)
        return {
            "total": len(devices),
            "devices": [d.model_dump(mode="json") for d in devices[:limit]],
        }


async def get_device(device_id: str) -> dict:
    """Full detail for one device by id."""
    async with session_scope() as session:
        return (await AgentService(session).get_device_view(device_id)).model_dump(mode="json")


async def fleet_health() -> dict:
    """Device counts by status and the 24h average inference latency (ms)."""
    async with session_scope() as session:
        svc = AgentService(session)
        health = await svc.agent_health()
        day_ago = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)
        latency = svc.avg_inference_latency_ms(day_ago)
        return {
            "total": health.total,
            "online": health.online,
            "degraded": health.degraded,
            "offline": health.offline,
            "provisioning": health.provisioning,
            "avg_inference_latency_ms_24h": latency,
        }


async def device_metrics(device_id: str, hours: int = 6, limit: int = 100) -> dict:
    """Recent telemetry samples for a device (cpu/gpu/mem/fps/latency)."""
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    async with session_scope() as session:
        rows = AgentService(session).list_metrics(device_id, since=since, limit=min(limit, 900))
    return {
        "device_id": device_id,
        "samples": [{**m, "recorded_at": m["recorded_at"].isoformat()} for m in rows],
    }


TOOLS = [list_devices, get_device, fleet_health, device_metrics]

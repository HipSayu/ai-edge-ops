"""Relay agent heartbeats to the WebSocket hub."""

from __future__ import annotations

from dqh.svc_core.messaging import Envelope

from app.core.events import event_bus
from app.core.ws import ws_hub
from app.modules.agent.event import HeartbeatRecorded
from app.shared.helpers.stats import average_or_none

_latest: dict[int, HeartbeatRecorded] = {}


def register() -> None:
    event_bus.subscribe(HeartbeatRecorded, _on_heartbeat)


async def _on_heartbeat(event: HeartbeatRecorded) -> None:
    _latest[event.device_id] = event
    await ws_hub.publish(
        f"telemetry/{event.device_id}",
        Envelope(
            type="telemetry.device",
            source="agent",
            payload={
                "device_id": event.device_id,
                "recorded_at": event.recorded_at.isoformat(),
                "cpu_percent": event.cpu_percent,
                "gpu_percent": event.gpu_percent,
                "mem_percent": event.mem_percent,
                "temperature_c": event.temperature_c,
                "fps": event.fps,
                "inference_latency_ms": event.inference_latency_ms,
            },
        ),
    )
    samples = list(_latest.values())
    await ws_hub.publish(
        "telemetry/agent",
        Envelope(
            type="telemetry.agent",
            source="agent",
            payload={
                "devices_reporting": len(samples),
                "fps_avg": average_or_none([s.fps for s in samples if s.fps is not None]),
                "inference_latency_ms_avg": average_or_none(
                    [s.inference_latency_ms for s in samples if s.inference_latency_ms is not None]
                ),
                "cpu_percent_avg": average_or_none([s.cpu_percent for s in samples if s.cpu_percent is not None]),
                "gpu_percent_avg": average_or_none([s.gpu_percent for s in samples if s.gpu_percent is not None]),
            },
        ),
    )


def reset_cache() -> None:
    _latest.clear()


__all__ = ["register", "reset_cache"]
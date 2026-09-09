"""Relay agent metrics to the WebSocket hub.

Two entry points feed the same fan-out:

* :func:`publish_sample` — called directly by the edge gateway for every
  fast-telemetry sample (``~1s``), never touches the DB.
* the :class:`HeartbeatRecorded` subscriber — the slower ``15s`` health
  heartbeat path, kept so dashboards still update if fast telemetry is off.

``telemetry/{device_id}`` carries per-device samples; ``telemetry/agent``
carries a rolling aggregate. New sockets ask for the current values with a
``{"op":"snapshot"}`` frame — see :func:`snapshot`.
"""

from __future__ import annotations

from typing import Any

from dqh.svc_core.messaging import Envelope

from app.core.ws import ws_hub
from app.modules.agent.event import HeartbeatRecorded
from app.shared.stats.average import average_or_none

_METRIC_KEYS = (
    "cpu_percent",
    "gpu_percent",
    "mem_percent",
    "mem_used_mb",
    "mem_total_mb",
    "disk_percent",
    "temperature_c",
    "fps",
    "inference_latency_ms",
)

# device_id -> latest sample dict (for snapshot-on-connect)
_latest: dict[int, dict[str, Any]] = {}


async def publish_sample(device_id: int, sample: dict[str, Any]) -> None:
    """Fan one metric sample out to the telemetry channel. ``sample`` needs a
    ``recorded_at`` (ISO string) plus any of :data:`_METRIC_KEYS`."""
    frame = {"device_id": device_id, **sample}
    _latest[device_id] = frame
    await ws_hub.publish(
        f"telemetry/{device_id}",
        Envelope(type="telemetry.device", source="agent", payload=frame),
    )
    await ws_hub.publish(
        "telemetry/agent",
        Envelope(type="telemetry.agent", source="agent", payload=_aggregate()),
    )


def snapshot() -> list[dict[str, Any]]:
    """Current per-device values — sent to a socket right after it connects."""
    return list(_latest.values())


def _aggregate() -> dict[str, Any]:
    samples = list(_latest.values())
    return {
        "devices_reporting": len(samples),
        "fps_avg": average_or_none([s["fps"] for s in samples if s.get("fps") is not None]),
        "inference_latency_ms_avg": average_or_none(
            [s["inference_latency_ms"] for s in samples if s.get("inference_latency_ms") is not None]
        ),
        "cpu_percent_avg": average_or_none(
            [s["cpu_percent"] for s in samples if s.get("cpu_percent") is not None]
        ),
        "gpu_percent_avg": average_or_none(
            [s["gpu_percent"] for s in samples if s.get("gpu_percent") is not None]
        ),
    }


async def on_heartbeat(event: HeartbeatRecorded) -> None:
    await publish_sample(
        event.device_id,
        {
            "recorded_at": event.recorded_at.isoformat(),
            **{key: getattr(event, key, None) for key in _METRIC_KEYS},
        },
    )


def reset_cache() -> None:
    _latest.clear()


__all__ = ["on_heartbeat", "publish_sample", "reset_cache", "snapshot"]

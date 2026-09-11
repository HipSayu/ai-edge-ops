"""In-memory fleet state — the *reported* half of each device.

Devices report themselves over MQTT (heartbeat + state); none of it is persisted.
On server restart the registry is empty and refills within one heartbeat interval
(and immediately from any retained ``state`` messages the broker replays). The
*desired* half — name, cameras, target model — lives in Postgres (``DeviceConfig``).
"""

from __future__ import annotations

import datetime as dt
from collections import deque
from dataclasses import dataclass, field

from dqh.svc_core.helpers.time import utcnow

from app.core.config import settings
from app.modules.agent.rules import DeviceStatus, evaluate_status

_SAMPLE_KEYS = (
    "cpu_percent", "gpu_percent", "mem_percent", "mem_used_mb", "mem_total_mb",
    "disk_percent", "temperature_c", "fps", "inference_latency_ms",
)
_RING = 900  # ~15 min at 1 Hz — enough for a page-load chart


@dataclass
class RuntimeState:
    last_seen_at: dt.datetime | None = None
    inference_latency_ms: float | None = None
    agent_version: str | None = None
    ip_address: str | None = None
    uptime_s: float | None = None
    backend: str | None = None
    arch: str | None = None
    active_image: str | None = None
    runtime_status: str = "unknown"  # applying | active | failed | unknown
    offline: bool = False  # set by the MQTT last-will / sweep
    samples: deque = field(default_factory=lambda: deque(maxlen=_RING))

    def status(self, *, now: dt.datetime | None = None) -> DeviceStatus:
        if self.offline:
            return DeviceStatus.OFFLINE
        return evaluate_status(
            last_seen_at=self.last_seen_at,
            now=now or utcnow(),
            offline_threshold_seconds=settings.offline_threshold_seconds,
            inference_latency_ms=self.inference_latency_ms,
            latency_slo_ms=settings.latency_slo_ms,
        )


@dataclass
class Transition:
    device_id: str
    old: DeviceStatus | None
    new: DeviceStatus


class FleetRegistry:
    def __init__(self) -> None:
        self._devices: dict[str, RuntimeState] = {}

    # --- writes (from the gateway) ---------------------------------------
    def record_heartbeat(self, device_id: str, hb) -> Transition | None:
        rs = self._devices.setdefault(device_id, RuntimeState())
        old = rs.status()
        rs.offline = False
        recorded_at = getattr(hb, "recorded_at", None) or utcnow()
        rs.last_seen_at = recorded_at
        rs.inference_latency_ms = hb.inference_latency_ms
        for f in ("agent_version", "ip_address", "uptime_s", "backend", "arch", "active_image"):
            if (v := getattr(hb, f, None)) is not None:
                setattr(rs, f, v)
        rs.samples.append(
            {"recorded_at": recorded_at, **{k: getattr(hb, k, None) for k in _SAMPLE_KEYS}}
        )
        return self._transition(device_id, old, rs.status())

    def recent_samples(
        self, device_id: str, *, since: dt.datetime | None = None, limit: int | None = None
    ) -> list[dict]:
        rs = self._devices.get(device_id)
        if rs is None:
            return []
        out = [s for s in rs.samples if since is None or s["recorded_at"] >= since]
        return out[-limit:] if limit else out

    def avg_latency(self, since: dt.datetime) -> float | None:
        vals = [
            s["inference_latency_ms"]
            for rs in self._devices.values()
            for s in rs.samples
            if s["recorded_at"] >= since and s["inference_latency_ms"] is not None
        ]
        return sum(vals) / len(vals) if vals else None

    def record_state(self, device_id: str, state) -> None:
        rs = self._devices.setdefault(device_id, RuntimeState())
        rs.offline = False
        rs.last_seen_at = utcnow()
        rs.runtime_status = state.runtime_status
        if state.active_image is not None:
            rs.active_image = state.active_image

    def mark_offline(self, device_id: str) -> Transition | None:
        rs = self._devices.get(device_id)
        if rs is None:
            return None
        old = rs.status()
        rs.offline = True
        return self._transition(device_id, old, DeviceStatus.OFFLINE)

    def forget(self, device_id: str) -> None:
        self._devices.pop(device_id, None)

    def sweep(self) -> list[Transition]:
        """Recompute statuses (call on a timer) — surfaces devices gone quiet."""
        now = utcnow()
        out: list[Transition] = []
        for device_id, rs in self._devices.items():
            # status() is pure; we only care that a caller re-reads it. Emit a
            # transition when a device crosses into OFFLINE without an explicit
            # will message.
            if rs.last_seen_at and not rs.offline:
                new = rs.status(now=now)
                if new is DeviceStatus.OFFLINE:
                    out.append(Transition(device_id, DeviceStatus.ONLINE, new))
        return out

    # --- reads ----------------------------------------------------------
    def get(self, device_id: str) -> RuntimeState | None:
        return self._devices.get(device_id)

    def all(self) -> dict[str, RuntimeState]:
        return dict(self._devices)

    def counts(self) -> dict[DeviceStatus, int]:
        out: dict[DeviceStatus, int] = {}
        for rs in self._devices.values():
            s = rs.status()
            out[s] = out.get(s, 0) + 1
        return out

    @staticmethod
    def _transition(device_id: str, old: DeviceStatus, new: DeviceStatus) -> Transition | None:
        return Transition(device_id, old, new) if new is not old else None


__all__ = ["FleetRegistry", "RuntimeState", "Transition"]

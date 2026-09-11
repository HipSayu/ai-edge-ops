"""Events published by the agent module."""

import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceRegistered:
    device_id: str
    name: str


@dataclass(frozen=True)
class DeviceWentOffline:
    device_id: str
    last_seen_at: dt.datetime | None


@dataclass(frozen=True)
class DeviceConfigChanged:
    """Operator changed a device's inference / camera config - re-push it."""

    device_id: str


@dataclass(frozen=True)
class DeviceLatencyDegraded:
    device_id: str
    inference_latency_ms: float
    slo_ms: float


@dataclass(frozen=True)
class HeartbeatRecorded:
    """Raised on every heartbeat, not just status transitions."""

    device_id: str
    recorded_at: dt.datetime
    cpu_percent: float | None
    gpu_percent: float | None
    mem_percent: float | None
    mem_used_mb: float | None
    mem_total_mb: float | None
    disk_percent: float | None
    temperature_c: float | None
    fps: float | None
    inference_latency_ms: float | None
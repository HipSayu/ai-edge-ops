"""Fleet domain: enums, events, pure business rules (no I/O)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from app.shared.enum import StrEnum


class DeviceStatus(StrEnum):
    PROVISIONING = "provisioning"  # registered, no heartbeat yet
    ONLINE = "online"
    DEGRADED = "degraded"  # heartbeating but breaching an SLO
    OFFLINE = "offline"  # no heartbeat within the threshold


# --- domain events -------------------------------------------------------------
@dataclass(frozen=True)
class DeviceRegistered:
    device_id: int
    name: str


@dataclass(frozen=True)
class DeviceWentOffline:
    device_id: int
    last_seen_at: dt.datetime | None


@dataclass(frozen=True)
class DeviceLatencyDegraded:
    device_id: int
    inference_latency_ms: float
    slo_ms: float


# --- pure rules ---------------------------------------------------------------
def evaluate_status(
    *,
    last_seen_at: dt.datetime | None,
    now: dt.datetime,
    offline_threshold_seconds: int,
    inference_latency_ms: float | None,
    latency_slo_ms: float,
) -> DeviceStatus:
    if last_seen_at is None:
        return DeviceStatus.PROVISIONING
    if (now - last_seen_at).total_seconds() > offline_threshold_seconds:
        return DeviceStatus.OFFLINE
    if inference_latency_ms is not None and inference_latency_ms > latency_slo_ms:
        return DeviceStatus.DEGRADED
    return DeviceStatus.ONLINE

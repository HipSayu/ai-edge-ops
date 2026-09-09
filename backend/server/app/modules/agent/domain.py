"""Agent domain rules and status model."""

import datetime as dt

from dqh.svc_core.helpers.str_enum import StrEnum


class DeviceStatus(StrEnum):
    PROVISIONING = "provisioning"
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"


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
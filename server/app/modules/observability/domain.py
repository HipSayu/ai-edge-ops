"""Observability domain: enums and events."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from app.shared.enum import StrEnum


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertType(StrEnum):
    DEVICE_OFFLINE = "device_offline"
    LATENCY_DEGRADED = "latency_degraded"
    PPE_VIOLATION = "ppe_violation"
    DEPLOYMENT_FAILED = "deployment_failed"


@dataclass(frozen=True)
class ViolationRecorded:
    violation_id: int
    device_id: int
    violation_type: str
    zone: str
    confidence: float
    recorded_at: dt.datetime


@dataclass(frozen=True)
class AlertRaised:
    alert_id: int
    type: AlertType
    severity: AlertSeverity
    device_id: int | None

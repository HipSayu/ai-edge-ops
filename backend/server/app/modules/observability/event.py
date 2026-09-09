"""Events published by the observability module."""

import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class ViolationRecorded:
    violation_id: int
    device_id: str
    violation_type: str
    zone: str
    confidence: float
    image_path: str | None
    recorded_at: dt.datetime


@dataclass(frozen=True)
class AlertRaised:
    alert_id: int
    type: str
    severity: str
    device_id: str | None
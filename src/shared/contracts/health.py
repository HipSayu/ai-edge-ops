"""Node-health early-warning messages (Edge → Cloud)."""

from datetime import datetime

from pydantic import Field

from src.shared.contracts.events import EdgeEvent
from src.shared.contracts.telemetry import TelemetryBase

ALARM_RAISED = "health.alarm.raised"
ALARM_CLEARED = "health.alarm.cleared"


class HealthPrediction(TelemetryBase):
    """`telemetry/health` — one score per sampling tick, plus the feature row it was computed from
    (the Cloud stores that row as the node's metric history)."""

    risk: float  # P(DEGRADED/CRITICAL within horizon_sec)
    alarm: bool
    threshold: float
    horizon_sec: float
    model_version: str
    features: dict[str, float | None] = Field(default_factory=dict)


class HealthAlarmEvent(EdgeEvent):
    """`event/health` — alarm raised/cleared (event_type = ALARM_RAISED | ALARM_CLEARED)."""

    alarm_started_at: datetime
    risk: float
    peak_risk: float
    model_version: str

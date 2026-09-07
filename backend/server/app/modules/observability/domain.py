"""Observability domain enums."""

from app.shared.helpers.enums import StrEnum


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


__all__ = ["AlertSeverity", "AlertStatus", "AlertType"]

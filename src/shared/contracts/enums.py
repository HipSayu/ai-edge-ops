"""Shared enumerations. Values mirror the PostgreSQL enum types in db/migrations."""

from enum import StrEnum


class NodeStatus(StrEnum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class ClusterStatus(StrEnum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class RuntimeStatus(StrEnum):
    CREATING = "CREATING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    RESTARTING = "RESTARTING"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class RuntimeType(StrEnum):
    VISION = "VISION"
    SAFETY = "SAFETY"
    ANOMALY = "ANOMALY"
    OCR = "OCR"
    CUSTOM = "CUSTOM"


class DeploymentStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REMOVING = "REMOVING"
    REMOVED = "REMOVED"


class CameraStatus(StrEnum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    FROZEN = "FROZEN"
    DISCONNECTED = "DISCONNECTED"


class OperationalState(StrEnum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class Severity(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

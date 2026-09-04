"""Envelope payload models."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


# --- edge -> server --------------------------------------------------------
class HeartbeatPayload(BaseModel):
    cpu_percent: float | None = None
    gpu_percent: float | None = None
    mem_percent: float | None = None
    temperature_c: float | None = None
    fps: float | None = None
    inference_latency_ms: float | None = None
    active_model_version_id: int | None = None
    recorded_at: dt.datetime | None = None


class TelemetryPayload(BaseModel):
    """Batched samples for higher-frequency metrics (charts, not health)."""

    samples: list[HeartbeatPayload] = Field(default_factory=list)


class ViolationPayload(BaseModel):
    zone: str
    violation_type: str
    confidence: float
    image_path: str | None = None
    recorded_at: dt.datetime | None = None


class StateReportPayload(BaseModel):
    active_model_version_id: int | None = None
    deployment_id: int | None = None
    runtime_status: str = "unknown"  # applying | active | failed
    config: dict = Field(default_factory=dict)
    detail: str | None = None


class CommandAckPayload(BaseModel):
    command_id: str
    deployment_id: int | None = None
    status: str  # accepted | in_progress | succeeded | failed
    detail: str | None = None


# --- server -> edge --------------------------------------------------------
class DeployModelPayload(BaseModel):
    command_id: str
    deployment_id: int
    model_version_id: int
    artifact_uri: str  # presigned URL or s3:// ref
    format: str
    checksum_sha256: str | None = None
    config: dict = Field(default_factory=dict)


class UpdateConfigPayload(BaseModel):
    command_id: str
    deployment_id: int | None = None
    config: dict


__all__ = [
    "CommandAckPayload",
    "DeployModelPayload",
    "HeartbeatPayload",
    "StateReportPayload",
    "TelemetryPayload",
    "UpdateConfigPayload",
    "ViolationPayload",
]

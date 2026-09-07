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


class BboxPayload(BaseModel):
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2, normalised [0, 1]


class BboxFramePayload(BaseModel):
    """One inferred video frame's detections, keyed to the WebRTC video track
    by ``frame_ts`` so a viewer can line the overlay up with the right frame
    despite this travelling over MQTT and the video over WebRTC — two
    independent, differently-paced transports.
    """

    camera_id: str
    frame_ts: float
    seq: int
    detections: list[BboxPayload] = Field(default_factory=list)


class StreamTokenRequestPayload(BaseModel):
    """Edge -> server RPC request: "let me publish this camera over WHIP".

    Sent over the existing (already-authenticated) MQTT link — see
    ``edge_agent.link.EdgeLink.request_stream_token`` — instead of a new HTTP
    call, since the edge device has no HTTP credential of its own.
    """

    camera_id: int  # server-side app.modules.camera.Camera.id


class StreamTokenReplyPayload(BaseModel):
    url: str
    path: str
    token: str
    expires_at: dt.datetime


class LogPayload(BaseModel):
    level: str
    logger: str
    message: str
    recorded_at: dt.datetime
    exception: str | None = None


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
    "BboxFramePayload",
    "BboxPayload",
    "StreamTokenReplyPayload",
    "StreamTokenRequestPayload",
    "CommandAckPayload",
    "DeployModelPayload",
    "HeartbeatPayload",
    "StateReportPayload",
    "TelemetryPayload",
    "UpdateConfigPayload",
    "ViolationPayload",
]

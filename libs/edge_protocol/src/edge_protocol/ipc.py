"""Agent <-> vision-runtime IPC contract.

The vision-runtime container and the edge agent run as sibling containers and
talk over a local unix socket. Messages are the same ``Envelope`` shape as the
MQTT protocol, newline-framed as JSON. The agent owns the MQTT identity; the
runtime only speaks this.

Frames / violations reuse the MQTT payloads (:class:`BboxFramePayload`,
:class:`ViolationPayload`); only the control messages are defined here.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# --- message types -------------------------------------------------------
T_VR_HELLO = "vr.hello"  # runtime -> agent, on connect
T_VR_HEALTH = "vr.health"  # runtime -> agent, periodic
T_VR_SET_CAMERAS = "vr.set_cameras"  # agent -> runtime
T_VR_STREAM_TOKEN = "vr.stream_token"  # agent -> runtime (reply to a request)
# runtime -> agent stream-token requests reuse T_STREAM_TOKEN_REQUEST
# runtime -> agent frames reuse T_BBOX_FRAME; violations reuse T_VIOLATION


class IpcCameraSpec(BaseModel):
    id: str
    source: str = "0"
    zone: str = "default"
    enabled: bool = True
    fps_limit: float = 10.0
    loop: bool = False
    camera_id: int | None = None  # server-side Camera.id, for streaming


class SetCamerasPayload(BaseModel):
    cameras: list[IpcCameraSpec] = Field(default_factory=list)
    ppe_required: list[str] = Field(default_factory=lambda: ["helmet", "vest"])
    conf_threshold: float = 0.25
    iou_threshold: float = 0.5
    imgsz: int = 640
    evidence_url: str | None = None  # POST endpoint for evidence uploads
    evidence_token: str | None = None
    streaming_enabled: bool = False
    encoder: str = "auto"
    bitrate_kbps: int = 2000


class CameraHealth(BaseModel):
    id: str
    running: bool
    fps: float | None = None
    last_frame_age_s: float | None = None
    streaming: bool = False
    detail: str | None = None


class WorkerHealthPayload(BaseModel):
    model_version: int | None = None
    cameras: list[CameraHealth] = Field(default_factory=list)


__all__ = [
    "T_VR_HEALTH",
    "T_VR_HELLO",
    "T_VR_SET_CAMERAS",
    "T_VR_STREAM_TOKEN",
    "CameraHealth",
    "IpcCameraSpec",
    "SetCamerasPayload",
    "WorkerHealthPayload",
]

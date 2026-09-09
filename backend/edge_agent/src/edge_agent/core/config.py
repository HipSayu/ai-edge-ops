"""Agent settings — one settings object, env with ``__`` delimiter.

    DEVICE_ID=cam-plant-a-01
    MQTT__HOST=mqtt.example.com   MQTT__PORT=8883   MQTT__TLS=true
    S3__ENDPOINT_URL=https://minio.example.com
    SERVER__BASE_URL=https://edgeops.example.com/api/v1
    CAMERAS__0__ID=bay-1   CAMERAS__0__SOURCE=rtsp://...
"""

from __future__ import annotations

from dqh.svc_core.config import BaseAppSettings, MqttConfig, S3Config
from pydantic import BaseModel, Field


class CameraConfig(BaseModel):
    id: str
    source: str = "0"          # rtsp url / device index / video file
    zone: str = "default"
    enabled: bool = True
    fps_limit: float = 10.0
    loop: bool = False          # replay a video file when it reaches EOF
    # app.modules.camera.Camera.id (server DB row) this local camera maps to.
    # Required only if streaming.enabled — see EdgeLink.request_stream_token.
    camera_id: int | None = None


class ServerConfig(BaseModel):
    base_url: str = "http://localhost:8000/api/v1"
    enroll_token: str | None = None
    request_timeout_s: float = 15.0


class StreamingConfig(BaseModel):
    enabled: bool = False
    kind: str = "ffmpeg"  # ffmpeg | null
    encoder: str = "auto"  # auto | v4l2m2m | vaapi | nvenc | <raw ffmpeg encoder name>
    bitrate_kbps: int = 2000


class ComposeConfig(BaseModel):
    """Image-based model deploy: the agent drives ``docker compose`` to pull and
    run the model image as the ``inference`` service."""

    project_dir: str = "/project"          # where compose.yml + env_file live
    env_file: str = "/project/.env"        # agent rewrites INFERENCE_IMAGE= here
    image_var: str = "INFERENCE_IMAGE"
    service: str = "inference"
    up_timeout_s: float = 180.0
    keep_previous_images: int = 1           # prune older than the last-known-good


class VisionConfig(BaseModel):
    """How this device turns cameras into detections + published video.

    Both fields accept ``auto`` (probe the host — see
    ``edge_agent.core.hardware.detect_hardware``) or an explicit override.
    """

    backend: str = "auto"  # auto | composed | deepstream
    device: str = "auto"   # auto | cpu | cuda:0 | mps
    runtime: str = "auto"  # auto (yolo if installed, else dummy) | yolo | dummy


class TelemetryConfig(BaseModel):
    """Fast metric stream, separate from the 15s health heartbeat.

    Samples are collected every ``sample_interval_s`` and flushed as a
    ``TelemetryPayload`` batch every ``flush_interval_s`` — the server fans
    these out to dashboards over WebSocket without touching the database.
    """

    enabled: bool = True
    sample_interval_s: float = 1.0
    flush_interval_s: float = 2.0


class InferenceConfig(BaseModel):
    weights_dir: str = "/var/lib/edge-agent/models"
    conf_threshold: float = 0.25
    iou_threshold: float = 0.5
    imgsz: int = 640
    classes: list[str] = Field(default_factory=lambda: ["helmet", "vest", "person"])
    ppe_required: list[str] = Field(default_factory=lambda: ["helmet", "vest"])


class AgentSettings(BaseAppSettings):
    service_name: str = "edge-agent"
    device_id: str = "edge-dev-0"

    heartbeat_interval_s: float = 15.0
    reconcile_interval_s: float = 30.0
    state_file: str = "/var/lib/edge-agent/state.json"
    outbox_file: str = "/var/lib/edge-agent/outbox.db"

    api_host: str = "0.0.0.0"
    api_port: int = 9100

    transport: str = "mqtt"    # mqtt | memory (tests)

    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    s3: S3Config = Field(default_factory=S3Config)
    server: ServerConfig = Field(default_factory=ServerConfig)
    inference: InferenceConfig = Field(default_factory=InferenceConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    streaming: StreamingConfig = Field(default_factory=StreamingConfig)
    compose: ComposeConfig = Field(default_factory=ComposeConfig)
    cameras: list[CameraConfig] = Field(default_factory=list)


def load_settings() -> AgentSettings:
    return AgentSettings()

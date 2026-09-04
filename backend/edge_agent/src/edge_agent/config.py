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


class ServerConfig(BaseModel):
    base_url: str = "http://localhost:8000/api/v1"
    enroll_token: str | None = None
    request_timeout_s: float = 15.0


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
    cameras: list[CameraConfig] = Field(default_factory=list)


def load_settings() -> AgentSettings:
    return AgentSettings()

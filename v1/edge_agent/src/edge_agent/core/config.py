"""Agent settings — one settings object, env with ``__`` delimiter.

    DEVICE_ID=cam-plant-a-01
    MQTT__HOST=mqtt.example.com   MQTT__PORT=8883   MQTT__TLS=true
    SERVER__BASE_URL=https://edgeops.example.com/api/v1
    CAMERAS__0__ID=bay-1   CAMERAS__0__SOURCE=rtsp://...

Inference (model, thresholds, GStreamer) lives in the vision-runtime container,
not here — the agent only supervises it (compose deploy) and relays its events.
"""

from __future__ import annotations

from dqh.svc_core.config import BaseAppSettings, MqttConfig
from pydantic import BaseModel, Field


class CameraConfig(BaseModel):
    id: str
    source: str = "0"          # rtsp url / device index / video file
    zone: str = "default"
    enabled: bool = True
    fps_limit: float = 10.0
    loop: bool = False          # replay a video file at EOF
    camera_id: int | None = None  # server-side Camera.id — required for streaming


class ServerConfig(BaseModel):
    base_url: str = "http://localhost:8000/api/v1"
    enroll_token: str | None = None
    request_timeout_s: float = 15.0


class ComposeConfig(BaseModel):
    """Image-based model deploy: the agent drives ``docker compose`` to pull and
    run the model image as the ``inference`` service."""

    project_dir: str = "/project"
    env_file: str = "/project/.env"
    image_var: str = "INFERENCE_IMAGE"
    service: str = "inference"
    up_timeout_s: float = 180.0
    keep_previous_images: int = 1


class VisionConfig(BaseModel):
    """Only the boot probe inputs — the runtime itself lives in the container.
    ``auto`` probes the host (see ``edge_agent.core.hardware.detect_hardware``)."""

    backend: str = "auto"  # auto | composed | deepstream
    device: str = "auto"   # auto | cpu | cuda:0 | mps


class TelemetryConfig(BaseModel):
    enabled: bool = True
    sample_interval_s: float = 1.0
    flush_interval_s: float = 2.0


class AgentSettings(BaseAppSettings):
    service_name: str = "edge"
    device_id: str = "edge-dev-0"

    heartbeat_interval_s: float = 15.0
    reconcile_interval_s: float = 30.0
    state_file: str = "/var/lib/edge/state.json"
    outbox_file: str = "/var/lib/edge/outbox.db"

    api_host: str = "0.0.0.0"
    api_port: int = 9100

    transport: str = "mqtt"    # mqtt | memory (tests)

    # vision-runtime IPC socket (shared volume with the inference container)
    inference_socket: str = "/run/edge/inference.sock"
    streaming_enabled: bool = False
    streaming_encoder: str = "auto"
    streaming_bitrate_kbps: int = 2000

    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    compose: ComposeConfig = Field(default_factory=ComposeConfig)
    cameras: list[CameraConfig] = Field(default_factory=list)


def load_settings() -> AgentSettings:
    return AgentSettings()

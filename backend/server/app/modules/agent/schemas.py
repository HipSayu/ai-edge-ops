"""Agent API contract."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from app.modules.agent.rules import DeviceStatus


class CameraSpec(BaseModel):
    id: str
    source: str
    zone: str = "default"
    fps_limit: int | None = None
    enabled: bool = True
    overrides: dict = Field(default_factory=dict)


class DeviceCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)  # operator-assigned, = box's DEVICE_ID
    name: str = Field(min_length=1, max_length=128)
    site: str = Field(min_length=1, max_length=128)
    labels: dict[str, str] = Field(default_factory=dict)
    desired_image: str | None = None
    cameras: list[CameraSpec] = Field(default_factory=list)


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    site: str | None = Field(default=None, max_length=128)
    labels: dict[str, str] | None = None
    desired_image: str | None = None
    cameras: list[CameraSpec] | None = None
    inference: dict | None = None
    agent_config: dict | None = None


class DeviceOut(BaseModel):
    """Merged view: desired config (Postgres) + reported runtime (FleetRegistry)."""

    device_id: str
    name: str
    site: str
    labels: dict
    desired_image: str | None
    cameras: list[CameraSpec]
    inference: dict
    agent_config: dict
    known: bool  # has a config row (vs. only ever seen over MQTT)
    # reported
    status: DeviceStatus
    last_seen_at: dt.datetime | None = None
    agent_version: str | None = None
    ip_address: str | None = None
    uptime_s: float | None = None
    backend: str | None = None
    arch: str | None = None
    active_image: str | None = None
    runtime_status: str = "unknown"
    in_sync: bool = False


class HeartbeatIn(BaseModel):
    recorded_at: dt.datetime | None = None  # defaults to server time
    backend: str | None = None
    arch: str | None = None
    cpu_percent: float | None = Field(default=None, ge=0, le=100)
    gpu_percent: float | None = Field(default=None, ge=0, le=100)
    mem_percent: float | None = Field(default=None, ge=0, le=100)
    mem_used_mb: float | None = Field(default=None, ge=0)
    mem_total_mb: float | None = Field(default=None, ge=0)
    disk_percent: float | None = Field(default=None, ge=0, le=100)
    temperature_c: float | None = None
    fps: float | None = Field(default=None, ge=0)
    inference_latency_ms: float | None = Field(default=None, ge=0)
    # agent identity / state (kept in FleetRegistry, not the sample)
    agent_version: str | None = None
    ip_address: str | None = None
    uptime_s: float | None = Field(default=None, ge=0)
    active_image: str | None = None


class MetricSample(BaseModel):
    recorded_at: dt.datetime
    cpu_percent: float | None = None
    gpu_percent: float | None = None
    mem_percent: float | None = None
    mem_used_mb: float | None = None
    mem_total_mb: float | None = None
    disk_percent: float | None = None
    temperature_c: float | None = None
    fps: float | None = None
    inference_latency_ms: float | None = None


class HeartbeatAck(BaseModel):
    device_id: str
    status: DeviceStatus
    sample: MetricSample


class AgentHealth(BaseModel):
    total: int = 0
    online: int = 0
    degraded: int = 0
    offline: int = 0
    provisioning: int = 0

"""Agent API contract."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from app.modules.agent.domain import DeviceStatus
from app.shared.schema import ORMSchema


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    site: str = Field(min_length=1, max_length=128)
    hardware: str = Field(min_length=1, max_length=64)
    ip_address: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)


class DeviceUpdate(BaseModel):
    site: str | None = Field(default=None, max_length=128)
    hardware: str | None = Field(default=None, max_length=64)
    ip_address: str | None = None
    labels: dict[str, str] | None = None


class DeviceOut(ORMSchema):
    id: int
    name: str
    site: str
    hardware: str
    ip_address: str | None
    status: DeviceStatus
    labels: dict
    last_seen_at: dt.datetime | None
    agent_version: str | None = None
    uptime_s: float | None = None
    active_model_version_id: int | None = None
    created_at: dt.datetime
    updated_at: dt.datetime


class HeartbeatIn(BaseModel):
    recorded_at: dt.datetime | None = None  # defaults to server time
    cpu_percent: float | None = Field(default=None, ge=0, le=100)
    gpu_percent: float | None = Field(default=None, ge=0, le=100)
    mem_percent: float | None = Field(default=None, ge=0, le=100)
    mem_used_mb: float | None = Field(default=None, ge=0)
    mem_total_mb: float | None = Field(default=None, ge=0)
    disk_percent: float | None = Field(default=None, ge=0, le=100)
    temperature_c: float | None = None
    fps: float | None = Field(default=None, ge=0)
    inference_latency_ms: float | None = Field(default=None, ge=0)
    # agent identity / state (persisted onto the Device row, not the sample)
    agent_version: str | None = None
    ip_address: str | None = None
    uptime_s: float | None = Field(default=None, ge=0)
    active_model_version_id: int | None = None


class MetricSampleOut(ORMSchema):
    id: int
    device_id: int
    recorded_at: dt.datetime
    cpu_percent: float | None
    gpu_percent: float | None
    mem_percent: float | None
    mem_used_mb: float | None
    mem_total_mb: float | None
    disk_percent: float | None
    temperature_c: float | None
    fps: float | None
    inference_latency_ms: float | None


class HeartbeatAck(BaseModel):
    device_id: int
    status: DeviceStatus
    sample: MetricSampleOut


class AgentHealth(BaseModel):
    total: int = 0
    online: int = 0
    degraded: int = 0
    offline: int = 0
    provisioning: int = 0

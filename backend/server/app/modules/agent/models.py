"""Agent ORM models: Device (aggregate root) and MetricSample."""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.persistence.sqlalchemy import DbEnum, TimestampMixin
from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.agent.rules import DeviceStatus


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    site: Mapped[str] = mapped_column(String(128), index=True)
    hardware: Mapped[str] = mapped_column(String(64))  # e.g. "Jetson Orin Nano 8GB"
    ip_address: Mapped[str | None] = mapped_column(String(64), default=None)
    status: Mapped[DeviceStatus] = mapped_column(
        DbEnum(DeviceStatus), default=DeviceStatus.PROVISIONING, index=True
    )
    labels: Mapped[dict] = mapped_column(JSON, default=dict)
    last_seen_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    # reported by the agent on every heartbeat (see AgentGateway._on_heartbeat)
    agent_version: Mapped[str | None] = mapped_column(String(32), default=None)
    uptime_s: Mapped[float | None] = mapped_column(Float, default=None)
    active_model_version_id: Mapped[int | None] = mapped_column(default=None)

    metric_samples: Mapped[list[MetricSample]] = relationship(
        back_populates="device", cascade="all, delete-orphan", passive_deletes=True
    )


class MetricSample(Base):
    __tablename__ = "metric_samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    recorded_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    cpu_percent: Mapped[float | None] = mapped_column(Float, default=None)
    gpu_percent: Mapped[float | None] = mapped_column(Float, default=None)
    mem_percent: Mapped[float | None] = mapped_column(Float, default=None)
    mem_used_mb: Mapped[float | None] = mapped_column(Float, default=None)
    mem_total_mb: Mapped[float | None] = mapped_column(Float, default=None)
    disk_percent: Mapped[float | None] = mapped_column(Float, default=None)
    temperature_c: Mapped[float | None] = mapped_column(Float, default=None)
    fps: Mapped[float | None] = mapped_column(Float, default=None)
    inference_latency_ms: Mapped[float | None] = mapped_column(Float, default=None)

    device: Mapped[Device] = relationship(back_populates="metric_samples")

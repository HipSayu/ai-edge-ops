"""Fleet ORM models: Device (aggregate root) and MetricSample."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.fleet.domain import DeviceStatus
from app.shared.enum import db_enum
from app.shared.models import TimestampMixin


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    site: Mapped[str] = mapped_column(String(128), index=True)
    hardware: Mapped[str] = mapped_column(String(64))  # e.g. "Jetson Orin Nano 8GB"
    ip_address: Mapped[str | None] = mapped_column(String(64), default=None)
    status: Mapped[DeviceStatus] = mapped_column(
        db_enum(DeviceStatus), default=DeviceStatus.PROVISIONING, index=True
    )
    labels: Mapped[dict] = mapped_column(JSON, default=dict)
    last_seen_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=None)

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
    temperature_c: Mapped[float | None] = mapped_column(Float, default=None)
    fps: Mapped[float | None] = mapped_column(Float, default=None)
    inference_latency_ms: Mapped[float | None] = mapped_column(Float, default=None)

    device: Mapped[Device] = relationship(back_populates="metric_samples")

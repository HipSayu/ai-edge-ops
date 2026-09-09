"""Agent ORM: Device — the *desired* config of an edge box (operator-owned).

The *reported* half (online, health, running image, probed hardware) is not
here — it lives in the in-memory :class:`app.modules.agent.fleet_registry.FleetRegistry`,
rebuilt from MQTT on every server start.
"""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.persistence.sqlalchemy import TimestampMixin
from sqlalchemy import JSON, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    # the string DEVICE_ID the box is provisioned with (also the MQTT identity)
    device_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    site: Mapped[str] = mapped_column(String(128), index=True)
    labels: Mapped[dict] = mapped_column(JSON, default=dict)

    # desired state pushed to the device
    desired_image: Mapped[str | None] = mapped_column(String(512), default=None)
    cameras: Mapped[list] = mapped_column(JSON, default=list)
    inference: Mapped[dict] = mapped_column(JSON, default=dict)   # sparse threshold overrides
    agent_config: Mapped[dict] = mapped_column(JSON, default=dict)  # log level, intervals


class MetricSample(Base):
    __tablename__ = "metric_samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
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

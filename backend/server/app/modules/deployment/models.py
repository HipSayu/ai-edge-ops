"""Deployment ORM model."""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.persistence.sqlalchemy import DbEnum, TimestampMixin
from sqlalchemy import JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.deployment.rules import DeploymentStatus


class Deployment(Base, TimestampMixin):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    model_version_id: Mapped[int] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[DeploymentStatus] = mapped_column(
        DbEnum(DeploymentStatus), default=DeploymentStatus.PENDING, index=True
    )
    # runtime inference config pushed to the device
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    note: Mapped[str | None] = mapped_column(Text, default=None)
    activated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=None)

"""Observability ORM: Violation and Alert."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.observability.domain import AlertSeverity, AlertStatus, AlertType
from app.shared.helpers.database import db_enum
from app.shared.models import TimestampMixin


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    zone: Mapped[str] = mapped_column(String(128), index=True)
    violation_type: Mapped[str] = mapped_column(String(64), index=True)  # "no_helmet", "no_vest"
    confidence: Mapped[float] = mapped_column(Float)
    image_path: Mapped[str | None] = mapped_column(String(512), default=None)
    recorded_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[AlertType] = mapped_column(db_enum(AlertType), index=True)
    severity: Mapped[AlertSeverity] = mapped_column(db_enum(AlertSeverity), index=True)
    status: Mapped[AlertStatus] = mapped_column(
        db_enum(AlertStatus), default=AlertStatus.OPEN, index=True
    )
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"), default=None, index=True
    )
    deployment_id: Mapped[int | None] = mapped_column(
        ForeignKey("deployments.id", ondelete="SET NULL"), default=None
    )
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    resolved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=None)

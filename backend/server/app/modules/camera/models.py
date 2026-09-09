"""Camera domain ORM models."""

from __future__ import annotations

from dqh.svc_core.persistence.sqlalchemy import TimestampMixin
from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Camera(Base, TimestampMixin):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(512))
    zone: Mapped[str] = mapped_column(String(128), default="default")
    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class CameraGroup(Base, TimestampMixin):
    __tablename__ = "camera_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    site: Mapped[str] = mapped_column(String(128), default="default")
    camera_ids: Mapped[list] = mapped_column(JSON, default=list)


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int | None] = mapped_column(
        ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True
    )
    image_path: Mapped[str] = mapped_column(String(512))
    captured_at: Mapped[str] = mapped_column(String(64))
    labels: Mapped[list] = mapped_column(JSON, default=list)

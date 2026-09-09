"""Model registry ORM: Model (aggregate root) and ModelVersion."""

from __future__ import annotations

from dqh.svc_core.persistence.sqlalchemy import DbEnum, TimestampMixin
from sqlalchemy import JSON, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.model_registry.rules import (
    CompressionMethod,
    ModelFormat,
    ModelTask,
    ModelVersionStatus,
)


class Model(Base, TimestampMixin):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    task: Mapped[ModelTask] = mapped_column(DbEnum(ModelTask), index=True)
    architecture: Mapped[str] = mapped_column(String(64))  # e.g. "yolo26-n"
    description: Mapped[str | None] = mapped_column(Text, default=None)

    versions: Mapped[list[ModelVersion]] = relationship(
        back_populates="model", cascade="all, delete-orphan", passive_deletes=True
    )


class ModelVersion(Base, TimestampMixin):
    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("model_id", "version", name="uq_model_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(
        ForeignKey("models.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[str] = mapped_column(String(32))  # e.g. "1.3.0"
    format: Mapped[ModelFormat] = mapped_column(DbEnum(ModelFormat))
    compression: Mapped[CompressionMethod] = mapped_column(
        DbEnum(CompressionMethod), default=CompressionMethod.NONE
    )
    status: Mapped[ModelVersionStatus] = mapped_column(
        DbEnum(ModelVersionStatus), default=ModelVersionStatus.DRAFT, index=True
    )
    artifact_uri: Mapped[str | None] = mapped_column(String(512), default=None)
    # OCI model-image refs (digest-pinned), one per edge backend variant. CI
    # builds both from the same weights; the gateway picks by device.backend.
    image_repo: Mapped[str | None] = mapped_column(String(512), default=None)
    image_cpu_digest: Mapped[str | None] = mapped_column(String(128), default=None)
    image_gpu_digest: Mapped[str | None] = mapped_column(String(128), default=None)
    size_mb: Mapped[float | None] = mapped_column(Float, default=None)
    # free-form eval metrics: {"mAP50_95": 0.41, "latency_ms": 7.8, "params_m": 2.1}
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)

    model: Mapped[Model] = relationship(back_populates="versions")

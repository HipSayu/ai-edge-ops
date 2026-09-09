"""Model registry API contract."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.modules.model_registry.rules import (
    CompressionMethod,
    ModelFormat,
    ModelTask,
    ModelVersionStatus,
)
from app.shared.schema import ORMSchema


class ModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    task: ModelTask
    architecture: str = Field(min_length=1, max_length=64)
    description: str | None = None


class ModelVersionCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    version: str = Field(min_length=1, max_length=32)
    format: ModelFormat
    compression: CompressionMethod = CompressionMethod.NONE
    image_repo: str | None = Field(default=None, max_length=512)
    image_cpu_digest: str | None = Field(default=None, max_length=128)
    image_gpu_digest: str | None = Field(default=None, max_length=128)
    size_mb: float | None = Field(default=None, ge=0)
    metrics: dict[str, float] = Field(default_factory=dict)


class ModelVersionOut(ORMSchema):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    model_id: int
    version: str
    format: ModelFormat
    compression: CompressionMethod
    status: ModelVersionStatus
    image_repo: str | None
    image_cpu_digest: str | None
    image_gpu_digest: str | None
    size_mb: float | None
    metrics: dict
    created_at: dt.datetime
    updated_at: dt.datetime


class ModelOut(ORMSchema):
    id: int
    name: str
    task: ModelTask
    architecture: str
    description: str | None
    created_at: dt.datetime
    updated_at: dt.datetime


class ModelWithVersions(ModelOut):
    versions: list[ModelVersionOut] = Field(default_factory=list)

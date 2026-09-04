"""Deployment API contract."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.modules.deployment.domain import DeploymentStatus
from app.shared.schema import ORMSchema


class DeploymentCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    device_id: int
    model_version_id: int
    config: dict = Field(default_factory=dict)
    note: str | None = None
    activate_now: bool = False


class DeploymentOut(ORMSchema):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    device_id: int
    model_version_id: int
    status: DeploymentStatus
    config: dict
    note: str | None
    activated_at: dt.datetime | None
    ended_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime


class DeploymentFailIn(BaseModel):
    reason: str = Field(min_length=1, max_length=512)

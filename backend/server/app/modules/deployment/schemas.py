"""Deployment API contract."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.modules.deployment.rules import DeploymentStatus
from app.shared.schema import ORMSchema


class DeploymentCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    device_id: int
    image: str = Field(min_length=1, max_length=512)  # a model tag or full ref
    config: dict = Field(default_factory=dict)
    note: str | None = None
    activate_now: bool = False


class DeploymentOut(ORMSchema):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    device_id: int
    image: str
    status: DeploymentStatus
    config: dict
    note: str | None
    activated_at: dt.datetime | None
    ended_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime


class DeploymentFailIn(BaseModel):
    reason: str = Field(min_length=1, max_length=512)

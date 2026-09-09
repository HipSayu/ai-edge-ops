"""Deployment API contract — deploy is a command, not a stored row."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class DeployRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    device_id: str
    image: str = Field(min_length=1, max_length=512)  # a model tag or full ref
    config: dict = Field(default_factory=dict)
    note: str | None = None


class DeploymentView(BaseModel):
    """Current deploy state of one device, derived from desired vs reported."""

    device_id: str
    name: str
    desired_image: str | None
    active_image: str | None
    runtime_status: str
    in_sync: bool
    updated_at: dt.datetime | None = None


class DeploymentFailIn(BaseModel):
    reason: str = Field(min_length=1, max_length=512)

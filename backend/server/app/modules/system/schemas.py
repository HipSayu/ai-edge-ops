"""System API schemas."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class SettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    value: dict
    created_at: dt.datetime
    updated_at: dt.datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: str
    actor: str
    detail: str | None
    created_at: str

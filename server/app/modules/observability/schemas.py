"""Observability API contract."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from app.modules.observability.domain import AlertSeverity, AlertStatus, AlertType
from app.shared.schema import ORMSchema


# --- violations --------------------------------------------------------------
class ViolationCreate(BaseModel):
    device_id: int
    zone: str = Field(min_length=1, max_length=128)
    violation_type: str = Field(min_length=1, max_length=64)
    confidence: float = Field(ge=0, le=1)
    image_path: str | None = None
    recorded_at: dt.datetime | None = None


class ViolationOut(ORMSchema):
    id: int
    device_id: int
    zone: str
    violation_type: str
    confidence: float
    image_path: str | None
    recorded_at: dt.datetime


# --- alerts ----------------------------------------------------------------
class AlertOut(ORMSchema):
    id: int
    type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    description: str | None
    device_id: int | None
    deployment_id: int | None
    context: dict
    resolved_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime


# --- analytics -----------------------------------------------------------
class OverviewKpis(BaseModel):
    devices_total: int
    devices_online: int
    active_deployments: int
    open_alerts: int
    violations_24h: int
    avg_inference_latency_ms: float | None


class TimeBucket(BaseModel):
    bucket: dt.date
    count: int


class LabelCount(BaseModel):
    label: str
    count: int

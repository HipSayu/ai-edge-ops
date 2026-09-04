"""Observability HTTP endpoints: violations, alerts, analytics."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, status

from app.api.deps import DbSession, Pagination
from app.core.pagination import Page
from app.modules.observability.domain import AlertStatus, AlertType
from app.modules.observability.schemas import (
    AlertOut,
    LabelCount,
    OverviewKpis,
    TimeBucket,
    ViolationCreate,
    ViolationOut,
)
from app.modules.observability.service import AlertService, AnalyticsService, ViolationService

router = APIRouter(tags=["observability"])


# --- violations --------------------------------------------------------------
@router.post("/violations", response_model=ViolationOut, status_code=status.HTTP_201_CREATED)
async def report_violation(data: ViolationCreate, db: DbSession) -> ViolationOut:
    """Called by the edge inference service each time a PPE violation is detected."""
    return ViolationOut.model_validate(await ViolationService(db).record(data))


@router.get("/violations", response_model=Page[ViolationOut])
async def list_violations(
    db: DbSession,
    params: Pagination,
    device_id: int | None = None,
    violation_type: str | None = None,
    since: dt.datetime | None = None,
) -> Page[ViolationOut]:
    page = await ViolationService(db).list(
        device_id=device_id, violation_type=violation_type, since=since, params=params
    )
    return Page.build(
        [ViolationOut.model_validate(v) for v in page.items], page.total, params
    )


# --- alerts ----------------------------------------------------------------
@router.get("/alerts", response_model=Page[AlertOut])
async def list_alerts(
    db: DbSession,
    params: Pagination,
    alert_status: AlertStatus | None = None,
    alert_type: AlertType | None = None,
    device_id: int | None = None,
) -> Page[AlertOut]:
    page = await AlertService(db).list(
        status=alert_status, alert_type=alert_type, device_id=device_id, params=params
    )
    return Page.build([AlertOut.model_validate(a) for a in page.items], page.total, params)


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(alert_id: int, db: DbSession) -> AlertOut:
    return AlertOut.model_validate(await AlertService(db).acknowledge(alert_id))


@router.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
async def resolve_alert(alert_id: int, db: DbSession) -> AlertOut:
    return AlertOut.model_validate(await AlertService(db).resolve(alert_id))


# --- analytics -----------------------------------------------------------
@router.get("/analytics/overview", response_model=OverviewKpis)
async def analytics_overview(db: DbSession) -> OverviewKpis:
    return await AnalyticsService(db).overview()


@router.get("/analytics/violations/timeseries", response_model=list[TimeBucket])
async def violations_timeseries(db: DbSession, days: int = 14) -> list[TimeBucket]:
    return await AnalyticsService(db).violations_timeseries(days)


@router.get("/analytics/violations/by-type", response_model=list[LabelCount])
async def violations_by_type(db: DbSession, days: int = 30) -> list[LabelCount]:
    return await AnalyticsService(db).violations_by_type(days)

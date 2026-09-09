"""Observability HTTP endpoints: violations, alerts, analytics."""

from __future__ import annotations

import asyncio
import datetime as dt
from pathlib import Path
from uuid import uuid4

from dqh.svc_core.transports.http import ApiResponse, Page, ok
from dqh.svc_core.transports.websocket.fastapi import serve_ws
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, WebSocket, status
from fastapi.responses import FileResponse

from app.api.deps import DbSession, Pagination
from app.core.config import settings
from app.core.ws import ws_hub
from app.core.ws_auth import authenticate_ws
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

MAX_EVIDENCE_BYTES = 10 * 1024 * 1024
ALLOWED_EVIDENCE_TYPES = {"image/jpeg", "image/png"}


@router.post("/evidence", include_in_schema=False)
async def upload_evidence(
    request: Request,
    file: UploadFile = File(...),
    device_id: str = Form(...),
    camera_id: str = Form(...),
    violation_type: str = Form(...),
    recorded_at: dt.datetime | None = Form(default=None),
) -> dict[str, str]:
    """Store a selected edge evidence frame and return its browser URL."""
    if file.content_type not in ALLOWED_EVIDENCE_TYPES:
        raise HTTPException(status_code=415, detail="evidence must be JPEG or PNG")

    content = await file.read(MAX_EVIDENCE_BYTES + 1)
    if len(content) > MAX_EVIDENCE_BYTES:
        raise HTTPException(status_code=413, detail="evidence image is too large")

    extension = ".png" if file.content_type == "image/png" else ".jpg"
    filename = f"{uuid4().hex}{extension}"
    evidence_dir = Path(settings.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    target = evidence_dir / filename
    await asyncio.to_thread(target.write_bytes, content)

    return {"image_path": str(request.url_for("get_evidence", filename=filename))}


@router.get("/evidence/{filename}", name="get_evidence", include_in_schema=False)
async def get_evidence(filename: str) -> FileResponse:
    """Serve an evidence image stored by the upload endpoint."""
    target = Path(settings.evidence_dir) / Path(filename).name
    if not target.is_file():
        raise HTTPException(status_code=404, detail="evidence not found")
    media_type = "image/png" if target.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(target, media_type=media_type)


# --- live updates ------------------------------------------------------------
@router.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket) -> None:
    """Live feed of newly-raised alerts."""
    await serve_ws(websocket, ws_hub, "alerts/#", authenticate=authenticate_ws)


# --- violations --------------------------------------------------------------
@router.post(
    "/violations", response_model=ApiResponse[ViolationOut], status_code=status.HTTP_201_CREATED
)
async def report_violation(data: ViolationCreate, db: DbSession) -> ApiResponse[ViolationOut]:
    """Called by the edge inference service each time a PPE violation is detected."""
    return ok(ViolationOut.model_validate(await ViolationService(db).record(data)))


@router.get("/violations", response_model=ApiResponse[Page[ViolationOut]])
async def list_violations(
    db: DbSession,
    params: Pagination,
    device_id: int | None = None,
    violation_type: str | None = None,
    since: dt.datetime | None = None,
) -> ApiResponse[Page[ViolationOut]]:
    page = await ViolationService(db).list(
        device_id=device_id, violation_type=violation_type, since=since, params=params
    )
    return ok(
        Page.of([ViolationOut.model_validate(v) for v in page.items], total=page.total, params=params)
    )


# --- alerts ----------------------------------------------------------------
@router.get("/alerts", response_model=ApiResponse[Page[AlertOut]])
async def list_alerts(
    db: DbSession,
    params: Pagination,
    alert_status: AlertStatus | None = None,
    alert_type: AlertType | None = None,
    device_id: int | None = None,
) -> ApiResponse[Page[AlertOut]]:
    page = await AlertService(db).list(
        status=alert_status, alert_type=alert_type, device_id=device_id, params=params
    )
    return ok(
        Page.of([AlertOut.model_validate(a) for a in page.items], total=page.total, params=params)
    )


@router.post("/alerts/{alert_id}/acknowledge", response_model=ApiResponse[AlertOut])
async def acknowledge_alert(alert_id: int, db: DbSession) -> ApiResponse[AlertOut]:
    return ok(AlertOut.model_validate(await AlertService(db).acknowledge(alert_id)))


@router.post("/alerts/{alert_id}/resolve", response_model=ApiResponse[AlertOut])
async def resolve_alert(alert_id: int, db: DbSession) -> ApiResponse[AlertOut]:
    return ok(AlertOut.model_validate(await AlertService(db).resolve(alert_id)))


# --- analytics -----------------------------------------------------------
@router.get("/analytics/overview", response_model=ApiResponse[OverviewKpis])
async def analytics_overview(db: DbSession) -> ApiResponse[OverviewKpis]:
    return ok(await AnalyticsService(db).overview())


@router.get("/analytics/violations/timeseries", response_model=ApiResponse[list[TimeBucket]])
async def violations_timeseries(db: DbSession, days: int = 14) -> ApiResponse[list[TimeBucket]]:
    return ok(await AnalyticsService(db).violations_timeseries(days))


@router.get("/analytics/violations/by-type", response_model=ApiResponse[list[LabelCount]])
async def violations_by_type(db: DbSession, days: int = 30) -> ApiResponse[list[LabelCount]]:
    return ok(await AnalyticsService(db).violations_by_type(days))

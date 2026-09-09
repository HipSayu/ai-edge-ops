"""Observability tools — PPE violations, alerts, analytics roll-ups."""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.transports.http import PaginationParams

from app.mcp._session import session_scope
from app.modules.observability import AlertService, AnalyticsService
from app.modules.observability.rules import AlertStatus, AlertType
from app.modules.observability.service import ViolationService


async def analytics_overview() -> dict:
    """Top-line KPIs: devices online/total, active deployments, open alerts,
    violations in the last 24h, average inference latency."""
    async with session_scope() as session:
        k = await AnalyticsService(session).overview()
        return k.model_dump()


async def list_alerts(
    status: str | None = None, alert_type: str | None = None, device_id: int | None = None,
    limit: int = 50,
) -> dict:
    """List alerts. status: open|acknowledged|resolved. alert_type:
    device_offline|latency_degraded|ppe_violation|deployment_failed."""
    st = AlertStatus(status) if status else None
    at = AlertType(alert_type) if alert_type else None
    async with session_scope() as session:
        page = await AlertService(session).list(
            status=st, alert_type=at, device_id=device_id,
            params=PaginationParams(page=1, page_size=min(limit, 200)),
        )
        return {
            "total": page.total,
            "alerts": [
                {
                    "id": a.id,
                    "type": str(a.type),
                    "severity": str(a.severity),
                    "status": str(a.status),
                    "title": a.title,
                    "device_id": a.device_id,
                    "deployment_id": a.deployment_id,
                    "created_at": a.created_at.isoformat(),
                    "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                }
                for a in page.items
            ],
        }


async def list_violations(
    device_id: int | None = None, violation_type: str | None = None, hours: int = 24,
    limit: int = 50,
) -> dict:
    """Recent PPE violations (no_helmet / no_vest ...), optionally by device or type."""
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    async with session_scope() as session:
        page = await ViolationService(session).list(
            device_id=device_id, violation_type=violation_type, since=since,
            params=PaginationParams(page=1, page_size=min(limit, 200)),
        )
        return {
            "total": page.total,
            "violations": [
                {
                    "id": v.id,
                    "device_id": v.device_id,
                    "zone": v.zone,
                    "violation_type": v.violation_type,
                    "confidence": v.confidence,
                    "recorded_at": v.recorded_at.isoformat(),
                }
                for v in page.items
            ],
        }


async def violations_by_type(days: int = 30) -> dict:
    """Violation counts grouped by type over the last N days."""
    async with session_scope() as session:
        rows = await AnalyticsService(session).violations_by_type(days=days)
        return {"days": days, "by_type": [r.model_dump() for r in rows]}


async def violations_timeseries(days: int = 14) -> dict:
    """Daily violation counts over the last N days."""
    async with session_scope() as session:
        rows = await AnalyticsService(session).violations_timeseries(days=days)
        return {"days": days, "buckets": [{"date": str(r.bucket), "count": r.count} for r in rows]}


TOOLS = [
    analytics_overview,
    list_alerts,
    list_violations,
    violations_by_type,
    violations_timeseries,
]

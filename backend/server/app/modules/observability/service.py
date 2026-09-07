"""Observability use-cases: violations, alerts, analytics."""

from __future__ import annotations

import datetime as dt

from dqh.svc_core.contracts.errors import NotFoundError
from dqh.svc_core.transports.http import Page
from dqh.svc_core.transports.http import PaginationParams as PageParams
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import event_bus
from app.shared.helpers.time import utcnow
from app.modules.observability.event import AlertRaised, ViolationRecorded
from app.modules.observability.domain import AlertSeverity, AlertStatus, AlertType
from app.modules.observability.models import Alert, Violation
from app.modules.observability.repository import AlertRepository, ViolationRepository
from app.modules.observability.schemas import (
    LabelCount,
    OverviewKpis,
    TimeBucket,
    ViolationCreate,
)


class ViolationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ViolationRepository(session)

    async def record(self, data: ViolationCreate) -> Violation:
        payload = data.model_dump()
        payload["recorded_at"] = data.recorded_at or utcnow()
        violation = Violation(**payload)
        await self.repo.add(violation)
        await self.session.commit()
        await event_bus.publish(
            ViolationRecorded(
                violation_id=violation.id,
                device_id=violation.device_id,
                violation_type=violation.violation_type,
                zone=violation.zone,
                confidence=violation.confidence,
                image_path=violation.image_path,
                recorded_at=violation.recorded_at,
            )
        )
        return violation

    async def list(
        self,
        *,
        device_id: int | None,
        violation_type: str | None,
        since: dt.datetime | None,
        params: PageParams,
    ) -> Page[Violation]:
        items, total = await self.repo.list_page(
            device_id=device_id, violation_type=violation_type, since=since, params=params
        )
        return Page.of(items, total=total, params=params)


class AlertService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AlertRepository(session)

    async def raise_alert(
        self,
        *,
        type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str | None = None,
        device_id: int | None = None,
        deployment_id: int | None = None,
        context: dict | None = None,
        dedupe: bool = True,
    ) -> Alert:
        """Create an alert, or return the existing un-resolved one for (type, device)."""
        if dedupe:
            existing = await self.repo.find_open(type, device_id)
            if existing is not None:
                return existing
        alert = Alert(
            type=type,
            severity=severity,
            title=title,
            description=description,
            device_id=device_id,
            deployment_id=deployment_id,
            context=context or {},
        )
        await self.repo.add(alert)
        await self.session.commit()
        await event_bus.publish(
            AlertRaised(alert_id=alert.id, type=type, severity=severity, device_id=device_id)
        )
        return alert

    async def get(self, alert_id: int) -> Alert:
        alert = await self.repo.get(alert_id)
        if alert is None:
            raise NotFoundError(f"alert {alert_id} not found")
        return alert

    async def list(
        self,
        *,
        status: AlertStatus | None,
        alert_type: AlertType | None,
        device_id: int | None,
        params: PageParams,
    ) -> Page[Alert]:
        items, total = await self.repo.list_page(
            status=status, alert_type=alert_type, device_id=device_id, params=params
        )
        return Page.of(items, total=total, params=params)

    async def acknowledge(self, alert_id: int) -> Alert:
        alert = await self.get(alert_id)
        if alert.status is AlertStatus.OPEN:
            alert.status = AlertStatus.ACKNOWLEDGED
            await self.session.commit()
        return alert

    async def resolve(self, alert_id: int) -> Alert:
        alert = await self.get(alert_id)
        if alert.status is not AlertStatus.RESOLVED:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = utcnow()
            await self.session.commit()
        return alert


class AnalyticsService:
    """Read-only roll-ups. Cross-module counts come from public services."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.violations = ViolationRepository(session)
        self.alerts = AlertRepository(session)

    async def overview(self) -> OverviewKpis:
        from app.modules.deployment.service import DeploymentService
        from app.modules.agent.service import AgentService

        now = utcnow()
        day_ago = now - dt.timedelta(hours=24)

        health = await AgentService(self.session).agent_health()
        avg_latency = await AgentService(self.session).avg_inference_latency_ms(day_ago)
        active_deployments = await DeploymentService(self.session).count_active()

        return OverviewKpis(
            devices_total=health.total,
            devices_online=health.online,
            active_deployments=active_deployments,
            open_alerts=await self.alerts.count_open(),
            violations_24h=await self.violations.count_since(day_ago),
            avg_inference_latency_ms=avg_latency,
        )

    async def violations_timeseries(self, days: int = 14) -> list[TimeBucket]:
        since = utcnow() - dt.timedelta(days=days)
        rows = await self.violations.daily_counts(since)
        return [TimeBucket(bucket=bucket, count=count) for bucket, count in rows]

    async def violations_by_type(self, days: int | None = 30) -> list[LabelCount]:
        since = utcnow() - dt.timedelta(days=days) if days else None
        rows = await self.violations.count_by_type(since)
        return [LabelCount(label=label, count=count) for label, count in rows]

"""Observability subscribers: turn domain events from other modules into alerts."""

from __future__ import annotations

from app.core.database import session_scope
from app.core.events import event_bus
from app.modules.deployment.domain import DeploymentFailed
from app.modules.fleet.domain import DeviceLatencyDegraded, DeviceWentOffline
from app.modules.observability.domain import AlertSeverity, AlertType, ViolationRecorded
from app.modules.observability.service import AlertService


def register() -> None:
    event_bus.subscribe(ViolationRecorded, _on_violation)
    event_bus.subscribe(DeviceWentOffline, _on_device_offline)
    event_bus.subscribe(DeviceLatencyDegraded, _on_latency_degraded)
    event_bus.subscribe(DeploymentFailed, _on_deployment_failed)


async def _on_violation(event: ViolationRecorded) -> None:
    async with session_scope() as session:
        await AlertService(session).raise_alert(
            type=AlertType.PPE_VIOLATION,
            severity=AlertSeverity.WARNING,
            title=f"PPE violation: {event.violation_type} in {event.zone}",
            device_id=event.device_id,
            context={"violation_id": event.violation_id, "confidence": event.confidence},
            dedupe=False,  # every violation is its own alert
        )


async def _on_device_offline(event: DeviceWentOffline) -> None:
    async with session_scope() as session:
        await AlertService(session).raise_alert(
            type=AlertType.DEVICE_OFFLINE,
            severity=AlertSeverity.CRITICAL,
            title="Edge device went offline",
            device_id=event.device_id,
            context={"last_seen_at": event.last_seen_at.isoformat() if event.last_seen_at else None},
        )


async def _on_latency_degraded(event: DeviceLatencyDegraded) -> None:
    async with session_scope() as session:
        await AlertService(session).raise_alert(
            type=AlertType.LATENCY_DEGRADED,
            severity=AlertSeverity.WARNING,
            title="Inference latency above SLO",
            device_id=event.device_id,
            context={"latency_ms": event.inference_latency_ms, "slo_ms": event.slo_ms},
        )


async def _on_deployment_failed(event: DeploymentFailed) -> None:
    async with session_scope() as session:
        await AlertService(session).raise_alert(
            type=AlertType.DEPLOYMENT_FAILED,
            severity=AlertSeverity.CRITICAL,
            title="Model deployment failed",
            device_id=event.device_id,
            deployment_id=event.deployment_id,
            context={"reason": event.reason},
            dedupe=False,
        )

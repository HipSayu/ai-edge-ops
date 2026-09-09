"""Observability's reactions to events from other modules.

Inbound: violations, device-offline, latency-degraded and failed deployments
all become alerts. Outbound: a raised alert is pushed to the browser over the
WebSocket hub.
"""

from __future__ import annotations

from dqh.svc_core.messaging import Envelope

from app.core.database import session_scope
from app.core.events import event_bus
from app.modules.agent.event import DeviceLatencyDegraded, DeviceWentOffline
from app.modules.deployment.event import DeploymentFailed
from app.modules.observability.domain import AlertSeverity, AlertType
from app.modules.observability.event import AlertRaised, ViolationRecorded
from app.modules.observability.schemas import AlertOut
from app.modules.observability.service import AlertService


class ObservabilitySubscribers:
    def register(self) -> None:
        event_bus.subscribe(ViolationRecorded, self._on_violation)
        event_bus.subscribe(DeviceWentOffline, self._on_device_offline)
        event_bus.subscribe(DeviceLatencyDegraded, self._on_latency_degraded)
        event_bus.subscribe(DeploymentFailed, self._on_deployment_failed)
        event_bus.subscribe(AlertRaised, self._on_alert_raised)

    async def _on_violation(self, event: ViolationRecorded) -> None:
        async with session_scope() as session:
            await AlertService(session).raise_alert(
                type=AlertType.PPE_VIOLATION,
                severity=AlertSeverity.WARNING,
                title=f"PPE violation: {event.violation_type} in {event.zone}",
                device_id=event.device_id,
                context={
                    "violation_id": event.violation_id,
                    "confidence": event.confidence,
                    "image_path": event.image_path,
                },
                dedupe=False,
            )

    async def _on_device_offline(self, event: DeviceWentOffline) -> None:
        async with session_scope() as session:
            await AlertService(session).raise_alert(
                type=AlertType.DEVICE_OFFLINE,
                severity=AlertSeverity.CRITICAL,
                title="Edge device went offline",
                device_id=event.device_id,
                context={
                    "last_seen_at": event.last_seen_at.isoformat()
                    if event.last_seen_at
                    else None
                },
            )

    async def _on_latency_degraded(self, event: DeviceLatencyDegraded) -> None:
        async with session_scope() as session:
            await AlertService(session).raise_alert(
                type=AlertType.LATENCY_DEGRADED,
                severity=AlertSeverity.WARNING,
                title="Inference latency above SLO",
                device_id=event.device_id,
                context={"latency_ms": event.inference_latency_ms, "slo_ms": event.slo_ms},
            )

    async def _on_deployment_failed(self, event: DeploymentFailed) -> None:
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

    async def _on_alert_raised(self, event: AlertRaised) -> None:
        from app.core.ws import ws_hub

        async with session_scope() as session:
            alert = await AlertService(session).get(event.alert_id)
            payload = AlertOut.model_validate(alert).model_dump(mode="json")
        await ws_hub.publish(
            f"alerts/{event.severity.value}",
            Envelope(type="alert.created", source="observability", payload=payload),
        )


def register() -> None:
    ObservabilitySubscribers().register()


__all__ = ["ObservabilitySubscribers", "register"]

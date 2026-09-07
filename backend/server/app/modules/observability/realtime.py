"""Publish observability alerts to the frontend WebSocket hub."""

from __future__ import annotations

from dqh.svc_core.messaging import Envelope

from app.core.database import session_scope
from app.core.events import event_bus
from app.core.ws import ws_hub
from app.modules.observability.event import AlertRaised
from app.modules.observability.schemas import AlertOut
from app.modules.observability.service import AlertService


def register() -> None:
    event_bus.subscribe(AlertRaised, _on_alert_raised)


async def _on_alert_raised(event: AlertRaised) -> None:
    async with session_scope() as session:
        alert = await AlertService(session).get(event.alert_id)
        payload = AlertOut.model_validate(alert).model_dump(mode="json")
    await ws_hub.publish(
        f"alerts/{event.severity.value}",
        Envelope(type="alert.created", source="observability", payload=payload),
    )


__all__ = ["register"]

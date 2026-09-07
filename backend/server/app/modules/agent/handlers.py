"""Agent subscribers to events from other modules."""

from __future__ import annotations

import logging

from app.core.database import session_scope
from app.core.events import event_bus
from app.modules.agent.repository import DeviceRepository
from app.modules.observability.event import ViolationRecorded

logger = logging.getLogger(__name__)


def register() -> None:
    event_bus.subscribe(ViolationRecorded, _on_violation_recorded)


async def _on_violation_recorded(event: ViolationRecorded) -> None:
    async with session_scope() as session:
        device = await DeviceRepository(session).get(event.device_id)
        if device is None:
            return
        if device.last_seen_at is None or event.recorded_at > device.last_seen_at:
            device.last_seen_at = event.recorded_at
            await session.commit()
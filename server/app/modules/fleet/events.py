"""Fleet subscribers to events from other modules."""

from __future__ import annotations

import logging

from app.core.database import session_scope
from app.core.events import event_bus
from app.modules.fleet.repository import DeviceRepository

logger = logging.getLogger(__name__)


def register() -> None:
    from app.modules.observability.domain import ViolationRecorded

    event_bus.subscribe(ViolationRecorded, _on_violation_recorded)


async def _on_violation_recorded(event: ViolationRecorded) -> None:  # noqa: F821
    """A violation implies the camera/device is alive — bump last_seen_at."""
    async with session_scope() as session:
        device = await DeviceRepository(session).get(event.device_id)
        if device is None:
            return
        if device.last_seen_at is None or event.recorded_at > device.last_seen_at:
            device.last_seen_at = event.recorded_at
            await session.commit()

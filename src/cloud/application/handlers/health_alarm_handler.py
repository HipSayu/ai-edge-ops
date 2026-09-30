import logging

from hopquangdo.messaging import Message
from pydantic import ValidationError

from src.cloud.application.ports.health_repository import HealthRepository
from src.shared.contracts import HealthAlarmEvent
from src.shared.contracts.health import ALARM_CLEARED, ALARM_RAISED

logger = logging.getLogger(__name__)


class HealthAlarmHandler:
    """Consumes `edge/+/+/event/health` and keeps node_health_alarms in step (the generic EdgeEventHandler
    still logs the event to node_logs)."""

    def __init__(self, health_repository: HealthRepository) -> None:
        self._health = health_repository

    async def handle(self, message: Message) -> None:
        try:
            event = HealthAlarmEvent.model_validate(message.payload_as_dict())
        except (ValidationError, ValueError) as exc:
            logger.warning("Invalid health alarm on %s: %s", message.topic, exc)
            return
        if event.event_type == ALARM_RAISED:
            await self._health.open_alarm(event)
        elif event.event_type == ALARM_CLEARED:
            await self._health.close_alarm(event)

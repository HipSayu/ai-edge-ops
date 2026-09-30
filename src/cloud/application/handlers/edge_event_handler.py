import logging

from hopquangdo.messaging import Message
from pydantic import ValidationError

from src.cloud.application.ports.event_repository import EventRepository
from src.shared.contracts import EdgeEvent

logger = logging.getLogger(__name__)


class EdgeEventHandler:
    """Consumes `edge/+/+/event/+` and persists every event to the node log."""

    def __init__(self, event_repository: EventRepository) -> None:
        self._event_repository = event_repository

    async def handle(self, message: Message) -> None:
        try:
            event = EdgeEvent.model_validate(message.payload_as_dict())
        except (ValidationError, ValueError) as exc:
            logger.warning("Invalid event on %s: %s", message.topic, exc)
            return
        await self._event_repository.append(event)

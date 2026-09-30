import logging

from hopquangdo.messaging import Message
from pydantic import ValidationError

from src.cloud.application.ports.runtime_log_repository import RuntimeLogRepository
from src.shared.contracts import RuntimeLogBatch

logger = logging.getLogger(__name__)


class RuntimeLogHandler:
    """Consumes `edge/+/+/logs/{runtime_id}` and keeps the recent lines per runtime."""

    def __init__(self, logs: RuntimeLogRepository) -> None:
        self._logs = logs

    async def handle(self, message: Message) -> None:
        try:
            batch = RuntimeLogBatch.model_validate(message.payload_as_dict())
        except (ValidationError, ValueError) as exc:
            logger.warning("Invalid log batch on %s: %s", message.topic, exc)
            return
        await self._logs.append(batch)

import logging

from hopquangdo.messaging import Message
from pydantic import BaseModel, ValidationError

from src.cloud.application.ports.health_repository import HealthRepository
from src.cloud.application.ports.telemetry_repository import TelemetryRepository
from src.shared.contracts import (
    EdgeTopics,
    GpuTelemetry,
    HealthPrediction,
    RuntimeTelemetry,
    SystemTelemetry,
    TelemetryKind,
)

logger = logging.getLogger(__name__)

_SCHEMAS: dict[str, type[BaseModel]] = {
    TelemetryKind.SYSTEM: SystemTelemetry,
    TelemetryKind.GPU: GpuTelemetry,
    TelemetryKind.RUNTIME: RuntimeTelemetry,
    TelemetryKind.HEALTH: HealthPrediction,
}


class TelemetryHandler:
    """Consumes `edge/+/+/telemetry/{kind}`, validates against the shared schema, stores raw samples in the hot
    store; health predictions (which carry the node's metric row) also go to the durable history."""

    def __init__(self, telemetry_repository: TelemetryRepository, health_repository: HealthRepository | None = None) -> None:
        self._telemetry_repository = telemetry_repository
        self._health_repository = health_repository

    async def handle(self, message: Message) -> None:
        address = EdgeTopics.parse(message.topic)
        schema = _SCHEMAS.get(address.kind or "")
        if schema is None:
            logger.debug("Unknown telemetry kind on %s", message.topic)
            return
        try:
            sample = schema.model_validate(message.payload_as_dict())
        except (ValidationError, ValueError) as exc:
            logger.warning("Invalid telemetry on %s: %s", message.topic, exc)
            return
        key = address.kind
        if isinstance(sample, RuntimeTelemetry):
            key = f"{address.kind}:{sample.runtime_id}"
        await self._telemetry_repository.record(address.node_id, address.kind, key, sample.model_dump(mode="json", exclude_none=True))
        if isinstance(sample, HealthPrediction) and self._health_repository is not None:
            await self._health_repository.record_prediction(address.cluster_id, sample)

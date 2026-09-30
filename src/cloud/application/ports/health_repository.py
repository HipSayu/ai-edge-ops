from typing import Protocol

from src.shared.contracts import HealthAlarmEvent, HealthPrediction


class HealthRepository(Protocol):
    """Durable node-health history: metric row + risk per tick, and alarm episodes."""

    async def record_prediction(self, cluster_id: str, prediction: HealthPrediction) -> None: ...

    async def open_alarm(self, event: HealthAlarmEvent) -> None: ...

    async def close_alarm(self, event: HealthAlarmEvent) -> None: ...

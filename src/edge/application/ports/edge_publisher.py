from typing import Protocol

from pydantic import BaseModel

from src.shared.contracts import EdgeEvent, EdgeTopics, NodeState, RuntimeLogBatch


class EdgePublisher(Protocol):
    """Reports this node's state, telemetry and events to the Cloud."""

    topics: EdgeTopics

    async def state(self, state: NodeState) -> None: ...

    async def telemetry(self, kind: str, sample: BaseModel) -> None: ...

    async def event(self, kind: str, event: EdgeEvent) -> None: ...

    async def logs(self, batch: RuntimeLogBatch) -> None: ...

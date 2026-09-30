from typing import Protocol

from src.edge.domain.entities.runtime_instance import RuntimeInstance


class DesiredStateRepository(Protocol):
    """Persists desired runtimes locally so the node keeps running them across agent restarts / offline periods."""

    async def load(self) -> list[RuntimeInstance]: ...

    async def save(self, instances: list[RuntimeInstance]) -> None: ...

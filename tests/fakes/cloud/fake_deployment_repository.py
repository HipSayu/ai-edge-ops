from __future__ import annotations

from src.cloud.domain.entities.deployment import Deployment
from src.shared.domain.clock import Clock


class FakeDeploymentRepository:
    def __init__(self) -> None:
        self._items: dict[str, Deployment] = {}

    async def add(self, deployment: Deployment) -> Deployment:
        deployment.created_at = deployment.updated_at = Clock.now()
        self._items[deployment.id] = deployment
        return deployment

    async def get(self, deployment_id: str) -> Deployment | None:
        return self._items.get(deployment_id)

    async def get_by_runtime(self, runtime_id: str) -> Deployment | None:
        matches = [d for d in self._items.values() if d.runtime_id == runtime_id]
        return max(matches, key=lambda d: d.created_at) if matches else None

    async def list(self, node_id: str | None = None) -> list[Deployment]:
        return [d for d in self._items.values() if node_id is None or d.node_id == node_id]

    async def save(self, deployment: Deployment) -> None:
        deployment.updated_at = Clock.now()
        self._items[deployment.id] = deployment

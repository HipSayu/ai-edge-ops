from __future__ import annotations

from typing import Protocol

from src.cloud.domain.entities.deployment import Deployment


class DeploymentRepository(Protocol):
    async def add(self, deployment: Deployment) -> Deployment: ...

    async def get(self, deployment_id: str) -> Deployment | None: ...

    async def get_by_runtime(self, runtime_id: str) -> Deployment | None: ...

    async def list(self, node_id: str | None = None) -> list[Deployment]: ...

    async def save(self, deployment: Deployment) -> None: ...

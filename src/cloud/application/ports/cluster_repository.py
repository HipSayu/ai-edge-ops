from __future__ import annotations

from typing import Protocol

from src.cloud.domain.entities.cluster import Cluster


class ClusterRepository(Protocol):
    async def add(self, cluster: Cluster) -> Cluster: ...

    async def get(self, cluster_id: str) -> Cluster | None: ...

    async def get_by_name(self, name: str) -> Cluster | None: ...

    async def list(self) -> list[Cluster]: ...

    async def save(self, cluster: Cluster) -> Cluster: ...

    async def delete(self, cluster_id: str) -> None:
        """Removes the cluster; its nodes, runtimes and deployments go with it (FK cascade)."""
        ...

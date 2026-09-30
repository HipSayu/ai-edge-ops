from __future__ import annotations

from src.cloud.domain.entities.cluster import Cluster
from src.shared.domain.clock import Clock


class FakeClusterRepository:
    def __init__(self) -> None:
        self._items: dict[str, Cluster] = {}

    async def add(self, cluster: Cluster) -> Cluster:
        cluster.created_at = cluster.updated_at = Clock.now()
        self._items[cluster.id] = cluster
        return cluster

    async def get(self, cluster_id: str) -> Cluster | None:
        return self._items.get(cluster_id)

    async def get_by_name(self, name: str) -> Cluster | None:
        return next((c for c in self._items.values() if c.name == name), None)

    async def list(self) -> list[Cluster]:
        return list(self._items.values())

    async def save(self, cluster: Cluster) -> Cluster:
        cluster.updated_at = Clock.now()
        self._items[cluster.id] = cluster
        return cluster

    async def delete(self, cluster_id: str) -> None:
        self._items.pop(cluster_id, None)

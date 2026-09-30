from __future__ import annotations

from datetime import datetime
from typing import Protocol

from src.cloud.domain.entities.node import Node
from src.cloud.domain.value_objects.node_heartbeat import NodeHeartbeat


class NodeRepository(Protocol):
    async def add(self, node: Node) -> Node: ...

    async def get(self, node_id: str) -> Node | None: ...

    async def list(self, cluster_id: str | None = None) -> list[Node]: ...

    async def save(self, node: Node) -> Node:
        """Persists the operator-editable fields (name, metadata)."""
        ...

    async def delete(self, node_id: str) -> None: ...

    async def apply_heartbeat(self, heartbeat: NodeHeartbeat) -> None: ...

    async def mark_offline_before(self, cutoff: datetime) -> list[str]:
        """Mark ONLINE/DEGRADED nodes whose last heartbeat is older than `cutoff` as OFFLINE."""
        ...

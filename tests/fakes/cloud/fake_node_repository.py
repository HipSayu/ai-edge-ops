from __future__ import annotations

from datetime import datetime

from src.cloud.domain.entities.node import Node
from src.cloud.domain.value_objects.node_heartbeat import NodeHeartbeat
from src.shared.contracts import NodeStatus
from src.shared.domain.clock import Clock


class FakeNodeRepository:
    def __init__(self) -> None:
        self._items: dict[str, Node] = {}

    async def add(self, node: Node) -> Node:
        node.created_at = node.updated_at = Clock.now()
        self._items[node.id] = node
        return node

    async def get(self, node_id: str) -> Node | None:
        return self._items.get(node_id)

    async def list(self, cluster_id: str | None = None) -> list[Node]:
        return [n for n in self._items.values() if cluster_id is None or n.cluster_id == cluster_id]

    async def save(self, node: Node) -> Node:
        node.updated_at = Clock.now()
        self._items[node.id] = node
        return node

    async def delete(self, node_id: str) -> None:
        self._items.pop(node_id, None)

    async def apply_heartbeat(self, hb: NodeHeartbeat) -> None:
        node = self._items.get(hb.node_id)
        if node is None:
            return
        node.status = hb.status
        node.last_heartbeat_at = hb.at
        for attr in ("agent_version", "hostname", "ip_address", "cpu_cores", "memory_total_mb", "gpu_name"):
            value = getattr(hb, attr)
            if value is not None:
                setattr(node, attr, value)
        node.updated_at = Clock.now()

    async def mark_offline_before(self, cutoff: datetime) -> list[str]:
        stale = []
        for node in self._items.values():
            alive = node.status in (NodeStatus.ONLINE, NodeStatus.DEGRADED)
            if alive and node.last_heartbeat_at is not None and node.last_heartbeat_at < cutoff:
                node.status = NodeStatus.OFFLINE
                stale.append(node.id)
        return stale

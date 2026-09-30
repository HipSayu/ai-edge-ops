import uuid
from typing import Any

from src.cloud.application.ports.cluster_repository import ClusterRepository
from src.cloud.application.ports.node_repository import NodeRepository
from src.cloud.application.ports.runtime_repository import RuntimeRepository
from src.cloud.domain.entities.cluster import Cluster
from src.cloud.domain.entities.node import Node
from src.cloud.domain.entities.runtime import Runtime
from src.shared.contracts import NodeStatus
from src.shared.exceptions import AppException, ErrorCode


class FleetService:
    """Use cases over the Cloud → Cluster → Node → Runtime hierarchy."""

    def __init__(self, clusters: ClusterRepository, nodes: NodeRepository, runtimes: RuntimeRepository) -> None:
        self._clusters = clusters
        self._nodes = nodes
        self._runtimes = runtimes

    # --- clusters ---
    async def create_cluster(
        self, name: str, description: str | None = None, location: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Cluster:
        if await self._clusters.get_by_name(name):
            raise AppException(ErrorCode.CONFLICT, f"Cluster '{name}' already exists")
        cluster = Cluster(
            id=str(uuid.uuid4()), name=name, description=description, location=location, metadata=metadata or {}
        )
        return await self._clusters.add(cluster)

    async def list_clusters(self) -> list[Cluster]:
        return await self._clusters.list()

    async def get_cluster(self, cluster_id: str) -> Cluster:
        cluster = await self._clusters.get(cluster_id)
        if cluster is None:
            raise AppException(ErrorCode.NOT_FOUND, f"Cluster {cluster_id} not found")
        return cluster

    async def update_cluster(self, cluster_id: str, changes: dict[str, Any]) -> Cluster:
        cluster = await self.get_cluster(cluster_id)
        name = changes.get("name")
        if name and name != cluster.name and await self._clusters.get_by_name(name):
            raise AppException(ErrorCode.CONFLICT, f"Cluster '{name}' already exists")
        for field in ("name", "description", "location", "metadata"):
            if field in changes:
                setattr(cluster, field, changes[field])
        return await self._clusters.save(cluster)

    async def delete_cluster(self, cluster_id: str) -> None:
        await self.get_cluster(cluster_id)
        for node in await self._nodes.list(cluster_id):
            await self._ensure_removable(node)
        await self._clusters.delete(cluster_id)

    # --- nodes ---
    async def update_node(self, node_id: str, changes: dict[str, Any]) -> Node:
        node = await self.get_node(node_id)
        name = changes.get("name")
        if name and name != node.name and any(n.name == name for n in await self._nodes.list(node.cluster_id)):
            raise AppException(ErrorCode.CONFLICT, f"Node '{name}' already exists in cluster {node.cluster_id}")
        for field in ("name", "metadata"):
            if field in changes:
                setattr(node, field, changes[field])
        return await self._nodes.save(node)

    async def delete_node(self, node_id: str) -> None:
        await self._ensure_removable(await self.get_node(node_id))
        await self._nodes.delete(node_id)

    async def _ensure_removable(self, node: Node) -> None:
        """Deleting a live node would orphan its runtimes on the edge: stop the agent / remove deployments first."""
        if node.status in (NodeStatus.ONLINE, NodeStatus.DEGRADED):
            raise AppException(ErrorCode.CONFLICT, f"Node '{node.name}' is {NodeStatus(node.status)}; stop its agent first")
        if await self._runtimes.list(node.id):
            raise AppException(ErrorCode.CONFLICT, f"Node '{node.name}' still has runtimes; remove its deployments first")

    async def register_node(
        self, cluster_id: str, name: str, metadata: dict[str, Any] | None = None
    ) -> Node:
        await self.get_cluster(cluster_id)
        if any(n.name == name for n in await self._nodes.list(cluster_id)):
            raise AppException(ErrorCode.CONFLICT, f"Node '{name}' already exists in cluster {cluster_id}")
        node = Node(id=str(uuid.uuid4()), cluster_id=cluster_id, name=name, metadata=metadata or {})
        return await self._nodes.add(node)

    async def list_nodes(self, cluster_id: str | None = None) -> list[Node]:
        return await self._nodes.list(cluster_id)

    async def get_node(self, node_id: str) -> Node:
        node = await self._nodes.get(node_id)
        if node is None:
            raise AppException(ErrorCode.NOT_FOUND, f"Node {node_id} not found")
        return node

    # --- runtimes ---
    async def list_runtimes(self, node_id: str | None = None) -> list[Runtime]:
        return await self._runtimes.list(node_id)

    async def get_runtime(self, runtime_id: str) -> Runtime:
        runtime = await self._runtimes.get(runtime_id)
        if runtime is None:
            raise AppException(ErrorCode.NOT_FOUND, f"Runtime {runtime_id} not found")
        return runtime

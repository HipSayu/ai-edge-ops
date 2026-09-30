"""What MCP tools return: each entity with the names of its cluster/node next to the ids, and without internals.

The assistant answers (and follow-up questions refer to things) by name, so results carry names; ids stay in
for the rare case a user needs one. `Directory` loads the names once per tool call.
"""

from dataclasses import dataclass
from typing import Any

from src.cloud.application.services.entity_resolver import cluster_code, node_code
from src.cloud.application.services.fleet_service import FleetService
from src.cloud.domain.entities.cluster import Cluster
from src.cloud.domain.entities.deployment import Deployment
from src.cloud.domain.entities.node import Node
from src.cloud.domain.entities.runtime import Runtime


@dataclass(frozen=True)
class Directory:
    clusters: dict[str, Cluster]
    nodes: dict[str, Node]
    runtimes: dict[str, Runtime]

    @classmethod
    async def load(cls, fleet: FleetService) -> "Directory":
        return cls(
            {c.id: c for c in await fleet.list_clusters()},
            {n.id: n for n in await fleet.list_nodes()},
            {r.id: r for r in await fleet.list_runtimes()},
        )

    def cluster_name(self, cluster_id: str) -> str | None:
        cluster = self.clusters.get(cluster_id)
        return cluster.name if cluster else None

    def node_name(self, node_id: str) -> str | None:
        node = self.nodes.get(node_id)
        return node.name if node else None


def cluster_view(cluster: Cluster, nodes: list[Node] | None = None) -> dict[str, Any]:
    view: dict[str, Any] = {
        "id": cluster.id, "name": cluster.name, "code": cluster_code(cluster), "status": cluster.status,
        "location": cluster.location, "description": cluster.description, "metadata": cluster.metadata,
    }
    if nodes is not None:
        view["nodes"] = {"total": len(nodes), "by_status": _count(n.status for n in nodes)}
    return view


def node_view(node: Node, directory: Directory) -> dict[str, Any]:
    return {
        "id": node.id, "name": node.name, "code": node_code(node),
        "cluster": directory.cluster_name(node.cluster_id), "cluster_id": node.cluster_id,
        "status": node.status, "last_heartbeat_at": node.last_heartbeat_at, "agent_version": node.agent_version,
        "hardware": {"cpu_cores": node.cpu_cores, "memory_total_mb": node.memory_total_mb, "gpu": node.gpu_name},
        "metadata": node.metadata,
    }


def runtime_view(runtime: Runtime, directory: Directory) -> dict[str, Any]:
    node = directory.nodes.get(runtime.node_id)
    return {
        "id": runtime.id, "name": runtime.name, "status": runtime.status, "type": runtime.type,
        "node": node.name if node else None, "cluster": directory.cluster_name(node.cluster_id) if node else None,
        "image": f"{runtime.image_uri}:{runtime.image_tag}" if runtime.image_uri else None,
        "model_id": runtime.model_id, "config": runtime.config, "started_at": runtime.started_at,
    }


def deployment_view(deployment: Deployment, directory: Directory) -> dict[str, Any]:
    spec = deployment.spec
    runtime = directory.runtimes.get(deployment.runtime_id)
    return {
        "id": deployment.id, "name": spec.get("name") or (runtime.name if runtime else None),
        "status": deployment.status, "message": deployment.message,
        "node": directory.node_name(deployment.node_id), "cluster": directory.cluster_name(deployment.cluster_id),
        "runtime_status": runtime.status if runtime else None,
        "image": f"{spec.get('image_uri')}:{spec.get('image_tag')}" if spec.get("image_uri") else None,
        "model_id": spec.get("model_id"), "config": spec.get("config") or {},
        "resource_limits": spec.get("resource_limits") or {}, "updated_at": deployment.updated_at,
    }


def _count(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts

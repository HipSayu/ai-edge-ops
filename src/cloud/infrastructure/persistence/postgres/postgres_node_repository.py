from __future__ import annotations

from datetime import datetime

from src.cloud.domain.entities.node import Node
from src.cloud.domain.value_objects.node_heartbeat import NodeHeartbeat
from src.cloud.infrastructure.persistence.postgres.postgres_repository import PostgresRepository


class PostgresNodeRepository(PostgresRepository[Node]):
    entity = Node

    async def add(self, node: Node) -> Node:
        return await self._one(
            """
            INSERT INTO nodes (id, cluster_id, name, status, metadata)
            VALUES ($1, $2, $3, $4::node_status, $5)
            RETURNING *
            """,
            node.id, node.cluster_id, node.name, node.status.value, node.metadata,
        )

    async def get(self, node_id: str) -> Node | None:
        return await self._one("SELECT * FROM nodes WHERE id = $1::uuid", node_id)

    async def save(self, node: Node) -> Node:
        return await self._one(
            "UPDATE nodes SET name = $2, metadata = $3 WHERE id = $1::uuid RETURNING *",
            node.id, node.name, node.metadata,
        )

    async def delete(self, node_id: str) -> None:
        await self._execute("DELETE FROM nodes WHERE id = $1::uuid", node_id)

    async def list(self, cluster_id: str | None = None) -> list[Node]:
        if cluster_id is None:
            return await self._many("SELECT * FROM nodes ORDER BY created_at")
        return await self._many(
            "SELECT * FROM nodes WHERE cluster_id = $1::uuid ORDER BY created_at", cluster_id
        )

    async def apply_heartbeat(self, hb: NodeHeartbeat) -> None:
        await self._execute(
            """
            UPDATE nodes SET
                status = $2::node_status,
                last_heartbeat_at = $3,
                agent_version = COALESCE($4, agent_version),
                hostname = COALESCE($5, hostname),
                ip_address = COALESCE($6::inet, ip_address),
                cpu_cores = COALESCE($7, cpu_cores),
                memory_total_mb = COALESCE($8, memory_total_mb),
                gpu_name = COALESCE($9, gpu_name)
            WHERE id = $1::uuid
            """,
            hb.node_id, hb.status.value, hb.at, hb.agent_version, hb.hostname, hb.ip_address,
            hb.cpu_cores, hb.memory_total_mb, hb.gpu_name,
        )

    async def mark_offline_before(self, cutoff: datetime) -> list[str]:
        rows = await self._db.pool.fetch(
            """
            UPDATE nodes SET status = 'OFFLINE'
            WHERE status IN ('ONLINE', 'DEGRADED') AND last_heartbeat_at < $1
            RETURNING id
            """,
            cutoff,
        )
        return [str(r["id"]) for r in rows]

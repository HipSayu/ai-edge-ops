from __future__ import annotations

from src.cloud.domain.entities.deployment import Deployment
from src.cloud.infrastructure.persistence.postgres.postgres_repository import PostgresRepository


class PostgresDeploymentRepository(PostgresRepository[Deployment]):
    entity = Deployment

    async def add(self, d: Deployment) -> Deployment:
        return await self._one(
            """
            INSERT INTO deployments (id, cluster_id, node_id, runtime_id, spec, status, last_command_id, message)
            VALUES ($1, $2, $3, $4, $5, $6::deployment_status, $7, $8)
            RETURNING *
            """,
            d.id, d.cluster_id, d.node_id, d.runtime_id, d.spec, d.status.value, d.last_command_id, d.message,
        )

    async def get(self, deployment_id: str) -> Deployment | None:
        return await self._one("SELECT * FROM deployments WHERE id = $1::uuid", deployment_id)

    async def get_by_runtime(self, runtime_id: str) -> Deployment | None:
        return await self._one(
            "SELECT * FROM deployments WHERE runtime_id = $1::uuid ORDER BY created_at DESC LIMIT 1", runtime_id
        )

    async def list(self, node_id: str | None = None) -> list[Deployment]:
        if node_id is None:
            return await self._many("SELECT * FROM deployments ORDER BY created_at DESC")
        return await self._many(
            "SELECT * FROM deployments WHERE node_id = $1::uuid ORDER BY created_at DESC", node_id
        )

    async def save(self, d: Deployment) -> None:
        await self._execute(
            """
            UPDATE deployments SET spec = $2, status = $3::deployment_status, last_command_id = $4, message = $5
            WHERE id = $1::uuid
            """,
            d.id, d.spec, d.status.value, d.last_command_id, d.message,
        )

from __future__ import annotations

from src.cloud.domain.entities.runtime import Runtime
from src.cloud.infrastructure.persistence.postgres.postgres_repository import PostgresRepository
from src.shared.contracts import RuntimeStatus


class PostgresRuntimeRepository(PostgresRepository[Runtime]):
    entity = Runtime

    async def add(self, runtime: Runtime) -> Runtime:
        return await self._one(
            """
            INSERT INTO runtimes (id, node_id, name, type, status, image_uri, image_tag, model_id,
                                  config, environment, resource_limits)
            VALUES ($1, $2, $3, $4::runtime_type, $5::runtime_status, $6, $7, $8::uuid, $9, $10, $11)
            RETURNING *
            """,
            runtime.id, runtime.node_id, runtime.name, runtime.type.value, runtime.status.value,
            runtime.image_uri, runtime.image_tag, runtime.model_id,
            runtime.config, runtime.environment, runtime.resource_limits,
        )

    async def get(self, runtime_id: str) -> Runtime | None:
        return await self._one("SELECT * FROM runtimes WHERE id = $1::uuid", runtime_id)

    async def list(self, node_id: str | None = None) -> list[Runtime]:
        if node_id is None:
            return await self._many("SELECT * FROM runtimes ORDER BY created_at")
        return await self._many(
            "SELECT * FROM runtimes WHERE node_id = $1::uuid ORDER BY created_at", node_id
        )

    async def save(self, runtime: Runtime) -> None:
        await self._execute(
            """
            UPDATE runtimes SET
                type = $2::runtime_type, image_uri = $3, image_tag = $4, model_id = $5::uuid,
                config = $6, environment = $7, resource_limits = $8
            WHERE id = $1::uuid
            """,
            runtime.id, runtime.type.value, runtime.image_uri, runtime.image_tag, runtime.model_id,
            runtime.config, runtime.environment, runtime.resource_limits,
        )

    async def update_status(self, runtime_id: str, status: RuntimeStatus, container_id: str | None = None) -> None:
        await self._execute(
            """
            UPDATE runtimes SET
                status = $2::runtime_status,
                container_id = COALESCE($3, container_id),
                started_at = CASE WHEN $2 = 'RUNNING' AND status <> 'RUNNING' THEN NOW() ELSE started_at END,
                stopped_at = CASE WHEN $2 IN ('STOPPED', 'FAILED') THEN NOW() ELSE stopped_at END
            WHERE id = $1::uuid
            """,
            runtime_id, status.value, container_id,
        )

    async def delete(self, runtime_id: str) -> None:
        await self._execute("DELETE FROM runtimes WHERE id = $1::uuid", runtime_id)

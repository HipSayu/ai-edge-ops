from __future__ import annotations

from src.cloud.domain.entities.cluster import Cluster
from src.cloud.infrastructure.persistence.postgres.postgres_repository import PostgresRepository


class PostgresClusterRepository(PostgresRepository[Cluster]):
    entity = Cluster

    async def add(self, cluster: Cluster) -> Cluster:
        return await self._one(
            """
            INSERT INTO clusters (id, name, description, status, location, metadata)
            VALUES ($1, $2, $3, $4::cluster_status, $5, $6)
            RETURNING *
            """,
            cluster.id, cluster.name, cluster.description, cluster.status.value, cluster.location, cluster.metadata,
        )

    async def get(self, cluster_id: str) -> Cluster | None:
        return await self._one("SELECT * FROM clusters WHERE id = $1::uuid", cluster_id)

    async def get_by_name(self, name: str) -> Cluster | None:
        return await self._one("SELECT * FROM clusters WHERE name = $1", name)

    async def list(self) -> list[Cluster]:
        return await self._many("SELECT * FROM clusters ORDER BY created_at")

    async def save(self, cluster: Cluster) -> Cluster:
        return await self._one(
            """
            UPDATE clusters SET name = $2, description = $3, location = $4, metadata = $5
            WHERE id = $1::uuid
            RETURNING *
            """,
            cluster.id, cluster.name, cluster.description, cluster.location, cluster.metadata,
        )

    async def delete(self, cluster_id: str) -> None:
        await self._execute("DELETE FROM clusters WHERE id = $1::uuid", cluster_id)

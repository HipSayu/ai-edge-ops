from __future__ import annotations

from typing import Any

from src.cloud.infrastructure.persistence.postgres.postgres_database import PostgresDatabase
from src.shared.contracts import EdgeEvent


class PostgresEventRepository:
    """Writes events to node_logs, and additionally to runtime_logs when a known runtime is referenced."""

    def __init__(self, db: PostgresDatabase) -> None:
        self._db = db

    async def append(self, event: EdgeEvent) -> None:
        payload = event.model_dump(mode="json")
        async with self._db.pool.acquire() as conn, conn.transaction():
            await conn.execute(
                """
                INSERT INTO node_logs (node_id, level, event_type, message, metadata, created_at)
                SELECT $1::uuid, $2::log_level, $3, $4, $5, $6
                WHERE EXISTS (SELECT 1 FROM nodes WHERE id = $1::uuid)
                """,
                event.node_id, event.severity.value, event.event_type, event.message, payload, event.timestamp,
            )
            if event.runtime_id:
                await conn.execute(
                    """
                    INSERT INTO runtime_logs (runtime_id, level, event_type, message, metadata, created_at)
                    SELECT $1::uuid, $2::log_level, $3, $4, $5, $6
                    WHERE EXISTS (SELECT 1 FROM runtimes WHERE id = $1::uuid)
                    """,
                    event.runtime_id, event.severity.value, event.event_type, event.message, payload,
                    event.timestamp,
                )

    async def list(self, node_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = await self._db.pool.fetch(
            """
            SELECT level, event_type, message, metadata, created_at FROM node_logs
            WHERE node_id = $1::uuid ORDER BY created_at DESC LIMIT $2
            """,
            node_id, limit,
        )
        return [dict(r) for r in rows]

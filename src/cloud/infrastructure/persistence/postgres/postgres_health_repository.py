from __future__ import annotations

from src.cloud.infrastructure.persistence.postgres.postgres_database import PostgresDatabase
from src.shared.contracts import HealthAlarmEvent, HealthPrediction

# node_metrics column <- feature name in the prediction row
_METRIC_COLUMNS = {
    "heartbeat_age_sec": "heartbeat_age_sec",
    "connection_error_count": "connection_reconnect_count",
    "cpu_usage_pct": "cpu_usage_pct",
    "memory_usage_pct": "memory_usage_pct",
    "gpu_usage_pct": "gpu_usage_pct",
    "gpu_temperature_c": "gpu_temperature_c",
    "disk_usage_pct": "disk_usage_pct",
    "inference_fps": "inference_fps",
    "inference_latency_ms": "inference_latency_ms",
    "runtime_restart_count": "runtime_restart_count",
    "runtime_error_count": "runtime_error_count",
}
_INT_COLUMNS = {"connection_error_count", "runtime_restart_count", "runtime_error_count"}


class PostgresHealthRepository:
    """Writes node_metrics / node_health_predictions (TimescaleDB hypertables) and node_health_alarms.
    Unknown nodes are skipped, like PostgresEventRepository; replays of the Edge outbox are idempotent."""

    def __init__(self, db: PostgresDatabase) -> None:
        self._db = db

    async def record_prediction(self, cluster_id: str, prediction: HealthPrediction) -> None:
        f = prediction.features
        values = [
            (int(round(f[src])) if col in _INT_COLUMNS else f[src]) if f.get(src) is not None else None
            for col, src in _METRIC_COLUMNS.items()
        ]
        extra = {k: v for k, v in f.items() if k not in _METRIC_COLUMNS.values()}
        cols = ", ".join(_METRIC_COLUMNS)
        params = ", ".join(f"${i}" for i in range(5, 5 + len(values)))
        async with self._db.pool.acquire() as conn, conn.transaction():
            await conn.execute(
                f"""
                INSERT INTO node_metrics (ts, node_id, cluster_id, extra, {cols})
                SELECT $1, $2::uuid, $3::uuid, $4, {params}
                WHERE EXISTS (SELECT 1 FROM nodes WHERE id = $2::uuid)
                ON CONFLICT (node_id, ts) DO NOTHING
                """,
                prediction.timestamp, prediction.node_id, cluster_id, extra, *values,
            )
            await conn.execute(
                """
                INSERT INTO node_health_predictions (ts, node_id, risk, alarm, threshold, model_version)
                SELECT $1, $2::uuid, $3, $4, $5, $6
                WHERE EXISTS (SELECT 1 FROM nodes WHERE id = $2::uuid)
                ON CONFLICT (node_id, ts) DO NOTHING
                """,
                prediction.timestamp, prediction.node_id, prediction.risk, prediction.alarm,
                prediction.threshold, prediction.model_version,
            )

    async def open_alarm(self, event: HealthAlarmEvent) -> None:
        await self._db.pool.execute(
            """
            INSERT INTO node_health_alarms (node_id, started_at, peak_risk, model_version)
            SELECT $1::uuid, $2, $3, $4
            WHERE EXISTS (SELECT 1 FROM nodes WHERE id = $1::uuid)
            ON CONFLICT (node_id, started_at) DO NOTHING
            """,
            event.node_id, event.alarm_started_at, event.peak_risk, event.model_version,
        )

    async def close_alarm(self, event: HealthAlarmEvent) -> None:
        await self._db.pool.execute(
            """
            UPDATE node_health_alarms SET ended_at = $3, peak_risk = GREATEST(peak_risk, $4)
            WHERE node_id = $1::uuid AND started_at = $2
            """,
            event.node_id, event.alarm_started_at, event.timestamp, event.peak_risk,
        )

from datetime import datetime, timedelta
from typing import Any

from src.cloud.application.ports.event_repository import EventRepository
from src.cloud.application.ports.runtime_log_repository import RuntimeLogRepository
from src.cloud.application.ports.telemetry_repository import TelemetryRepository
from src.cloud.application.services.fleet_service import FleetService
from src.shared.contracts import NodeStatus, TelemetryKind
from src.shared.domain.clock import Clock


class MonitoringService:
    def __init__(
        self,
        fleet: FleetService,
        telemetry_repository: TelemetryRepository,
        event_repository: EventRepository,
        runtime_logs: RuntimeLogRepository,
    ) -> None:
        self._fleet = fleet
        self._telemetry_repository = telemetry_repository
        self._event_repository = event_repository
        self._runtime_logs = runtime_logs

    async def fleet_metrics(self, points: int = 30, bucket_sec: int = 10) -> list[dict[str, Any]]:
        """Fleet-wide series for the overview charts, oldest first, from each node's recent telemetry.

        Per bucket: summed inference fps and detections, mean latency and GPU use over the nodes
        that reported, and how many nodes reported at all.
        """
        now = Clock.now()
        start = now - timedelta(seconds=points * bucket_sec)
        buckets = [
            {"fps": 0.0, "throughput": 0.0, "latency": [], "gpu": [], "nodes": set()} for _ in range(points)
        ]

        def bucket_of(sample: dict[str, Any]) -> dict[str, Any] | None:
            try:
                at = datetime.fromisoformat(str(sample["timestamp"]).replace("Z", "+00:00"))
            except (KeyError, ValueError):
                return None
            index = int((at - start).total_seconds() // bucket_sec)
            return buckets[index] if 0 <= index < points else None

        history = points * bucket_sec // 5 + 5  # agents report every ~5 s
        clusters = await self._fleet.list_clusters()
        nodes = await self._fleet.list_nodes()
        for node in nodes:
            for sample in await self._telemetry_repository.history(node.id, TelemetryKind.SYSTEM, history):
                if (b := bucket_of(sample)) is not None:
                    b["nodes"].add(node.id)
            for sample in await self._telemetry_repository.history(node.id, TelemetryKind.GPU, history):
                if (b := bucket_of(sample)) is not None and sample.get("gpu_usage_pct") is not None:
                    b["gpu"].append(sample["gpu_usage_pct"])
            for sample in await self._telemetry_repository.history(node.id, TelemetryKind.RUNTIME, history * 4):
                if (b := bucket_of(sample)) is None:
                    continue
                b["fps"] += sample.get("inference_fps") or 0
                b["throughput"] += sample.get("detection_count") or 0
                if sample.get("inference_latency_ms") is not None:
                    b["latency"].append(sample["inference_latency_ms"])

        online_by_cluster: dict[str, list[bool]] = {}
        for node in nodes:
            online_by_cluster.setdefault(node.cluster_id, []).append(node.status in (NodeStatus.ONLINE,))
        healthy = sum(1 for c in clusters if (flags := online_by_cluster.get(c.id)) and all(flags))

        def mean(xs: list[float]) -> float:
            return round(sum(xs) / len(xs), 1) if xs else 0.0

        return [
            {
                "time": (start + timedelta(seconds=(i + 1) * bucket_sec)).strftime("%H:%M:%S"),
                "fps": round(b["fps"], 1),
                "latency": mean(b["latency"]),
                "throughput": round(b["throughput"], 1),
                "gpu": mean(b["gpu"]),
                "alert": 0,
                "healthyClusters": healthy,
                "onlineNodes": len(b["nodes"]),
                "onlineCameras": 0,
            }
            for i, b in enumerate(buckets)
        ]

    async def runtime_logs(self, runtime_id: str, limit: int) -> list[dict[str, Any]]:
        await self._fleet.get_runtime(runtime_id)
        return await self._runtime_logs.recent(runtime_id, limit)

    async def latest(self, node_id: str) -> dict[str, dict[str, Any]]:
        await self._fleet.get_node(node_id)
        return await self._telemetry_repository.latest(node_id)

    async def history(self, node_id: str, kind: str, limit: int) -> list[dict[str, Any]]:
        await self._fleet.get_node(node_id)
        return await self._telemetry_repository.history(node_id, kind, limit)

    async def events(self, node_id: str, limit: int) -> list[dict[str, Any]]:
        await self._fleet.get_node(node_id)
        return await self._event_repository.list(node_id, limit)

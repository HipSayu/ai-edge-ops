"""Edge -> Cloud reporting: node state (heartbeat), telemetry, and runtime container logs."""

import logging
from collections.abc import Callable, Sequence
from datetime import datetime

from hopquangdo.containers import ContainerEngine
from pydantic import BaseModel

from src.edge.application.ports.edge_publisher import EdgePublisher
from src.edge.application.ports.gpu_collector import GpuCollector
from src.edge.application.ports.node_info_provider import NodeInfoProvider
from src.edge.application.ports.system_collector import SystemCollector
from src.edge.application.services.runtime_containers import RuntimeContainers
from src.edge.application.services.runtime_service import RuntimeService
from src.shared.contracts import (
    EdgeEvent,
    EventKind,
    NodeState,
    NodeStatus,
    RuntimeLogBatch,
    RuntimeStatus,
    RuntimeTelemetry,
    Severity,
    TelemetryKind,
)

logger = logging.getLogger(__name__)

_UNHEALTHY = {RuntimeStatus.FAILED, RuntimeStatus.DEGRADED}


class StateReportService:
    """Builds and publishes the node's reported state (retained) — doubles as heartbeat."""

    def __init__(
        self,
        cluster_id: str,
        node_id: str,
        agent_version: str,
        runtime_service: RuntimeService,
        info: NodeInfoProvider,
        publisher: EdgePublisher,
    ) -> None:
        self._cluster_id = cluster_id
        self._node_id = node_id
        self._agent_version = agent_version
        self._runtime_service = runtime_service
        self._info = info
        self._publisher = publisher

    def agent_status(self) -> NodeStatus:
        if any(i.status in _UNHEALTHY and i.desired_running for i in self._runtime_service.list()):
            return NodeStatus.DEGRADED
        return NodeStatus.ONLINE

    def build(self, status: NodeStatus | None = None) -> NodeState:
        info = self._info.info()
        return NodeState(
            cluster_id=self._cluster_id,
            node_id=self._node_id,
            agent_status=status or self.agent_status(),
            agent_version=self._agent_version,
            hostname=info.hostname,
            ip_address=info.ip_address,
            cpu_cores=info.cpu_cores,
            memory_total_mb=info.memory_total_mb,
            gpu_name=info.gpu_name,
            runtimes=self._runtime_service.snapshot(),
        )

    async def publish(self, status: NodeStatus | None = None) -> NodeState:
        state = self.build(status)
        await self._publisher.state(state)
        return state


class TelemetryReportService:
    """Publishes node telemetry on a timer and relays runtime-reported telemetry/events (Runtime → Agent → Cloud)."""

    def __init__(
        self,
        node_id: str,
        publisher: EdgePublisher,
        runtime_service: RuntimeService,
        system: SystemCollector,
        gpu: GpuCollector,
        observers: Sequence[Callable[[str, BaseModel], None]] = (),
    ) -> None:
        self._node_id = node_id
        self._observers = list(observers)  # e.g. HealthService.observe; sees every sample before it is sent
        self._publisher = publisher
        self._runtime_service = runtime_service
        self._system = system
        self._gpu = gpu

    def _observe(self, kind: str, sample: BaseModel) -> None:
        for observer in self._observers:
            try:
                observer(kind, sample)
            except Exception:
                logger.exception("Telemetry observer failed")

    async def publish_node_telemetry(self) -> None:
        gpu = await self._gpu.collect(self._node_id)
        if gpu is not None:
            self._observe(TelemetryKind.GPU, gpu)
            await self._publisher.telemetry(TelemetryKind.GPU, gpu)
        system = await self._system.collect(self._node_id)
        self._observe(TelemetryKind.SYSTEM, system)
        await self._publisher.telemetry(TelemetryKind.SYSTEM, system)

    async def relay_runtime_telemetry(self, runtime_id: str, sample: RuntimeTelemetry) -> None:
        instance = self._runtime_service.get(runtime_id)  # raises AppException(NOT_FOUND) for unknown runtimes
        enriched = sample.model_copy(
            update={
                "node_id": self._node_id,
                "runtime_id": runtime_id,
                "runtime_status": sample.runtime_status or instance.status,
                "runtime_restart_count": instance.restart_count,
            }
        )
        if enriched.effective_fps_ratio is None and enriched.inference_fps is not None and enriched.target_fps:
            enriched.effective_fps_ratio = round(enriched.inference_fps / enriched.target_fps, 4)
        self._observe(TelemetryKind.RUNTIME, enriched)
        await self._publisher.telemetry(TelemetryKind.RUNTIME, enriched)

    async def relay_runtime_event(self, runtime_id: str, event_type: str, message: str,
                                  severity: Severity, data: dict) -> None:
        self._runtime_service.get(runtime_id)
        kind = EventKind.ERROR if severity in (Severity.ERROR, Severity.CRITICAL) else EventKind.RUNTIME
        await self._publisher.event(
            kind,
            EdgeEvent(node_id=self._node_id, runtime_id=runtime_id, event_type=event_type, message=message,
                      severity=severity, data=data),
        )


class RuntimeLogService:
    """Ships new container log lines of every runtime to the Cloud, one batch per runtime per tick."""

    def __init__(
        self,
        node_id: str,
        runtime_service: RuntimeService,
        engine: ContainerEngine,
        publisher: EdgePublisher,
        batch_limit: int = 200,
    ) -> None:
        self._node_id = node_id
        self._runtimes = runtime_service
        self._engine = engine
        self._publisher = publisher
        self._batch_limit = batch_limit
        self._cursors: dict[str, datetime] = {}  # runtime id -> timestamp of the last shipped line

    async def ship(self) -> None:
        live = {i.runtime_id for i in self._runtimes.list()}
        for runtime_id in list(self._cursors):
            if runtime_id not in live:  # removed runtime: forget its cursor
                del self._cursors[runtime_id]
        for instance in self._runtimes.list():
            if not instance.container_id:
                continue
            try:
                raw = await self._engine.logs(
                    instance.container_id, self._cursors.get(instance.runtime_id), self._batch_limit
                )
            except Exception as exc:
                logger.debug("Log read failed for %s: %s", instance.runtime_id, exc)
                continue
            if not raw:
                continue
            lines = [RuntimeContainers.to_log_line(line) for line in raw]
            self._cursors[instance.runtime_id] = lines[-1].timestamp
            await self._publisher.logs(
                RuntimeLogBatch(
                    node_id=self._node_id, runtime_id=instance.runtime_id, runtime_name=instance.spec.name,
                    lines=lines,
                )
            )

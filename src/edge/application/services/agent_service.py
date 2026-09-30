import asyncio
import logging

from hopquangdo.messaging import PubSub

from src.edge.application.ports.edge_publisher import EdgePublisher
from src.edge.application.services.command_service import CommandService
from src.edge.application.services.health_service import HealthService
from src.edge.application.services.reporting import RuntimeLogService, StateReportService, TelemetryReportService
from src.edge.application.services.runtime_service import RuntimeService
from src.edge.domain.entities.runtime_instance import RuntimeInstance
from src.shared.application.periodic import run_every
from src.shared.contracts import EdgeEvent, EventKind, NodeStatus, RuntimeStatus, Severity

logger = logging.getLogger(__name__)


class AgentService:
    """Node-level control loop: command intake, reconciliation, state heartbeat and telemetry."""

    def __init__(
        self,
        node_id: str,
        pubsub: PubSub,
        publisher: EdgePublisher,
        runtime_service: RuntimeService,
        command_service: CommandService,
        state_report_service: StateReportService,
        telemetry_report_service: TelemetryReportService,
        runtime_log_service: RuntimeLogService,
        state_interval_sec: float = 10.0,
        telemetry_interval_sec: float = 5.0,
        reconcile_interval_sec: float = 15.0,
        log_interval_sec: float = 5.0,
        health_service: HealthService | None = None,
    ) -> None:
        self.node_id = node_id
        self._pubsub = pubsub
        self._publisher = publisher
        self.runtime_service = runtime_service
        self.command_service = command_service
        self.state_report_service = state_report_service
        self.telemetry_report_service = telemetry_report_service
        self.runtime_log_service = runtime_log_service
        self.health_service = health_service
        self._intervals = (state_interval_sec, telemetry_interval_sec, reconcile_interval_sec, log_interval_sec)
        self._tasks: list[asyncio.Task] = []
        runtime_service.on_status_change(self._on_runtime_status)

    async def start(self) -> None:
        await self._pubsub.connect()
        await self.runtime_service.restore()
        await self._pubsub.subscribe(self._publisher.topics.commands(), self.command_service.handle)
        await self.state_report_service.publish()
        state_s, telemetry_s, reconcile_s, logs_s = self._intervals
        self._tasks = [
            asyncio.create_task(run_every(state_s, self.state_report_service.publish), name="state"),
            asyncio.create_task(run_every(telemetry_s, self.telemetry_report_service.publish_node_telemetry),
                                name="telemetry"),
            asyncio.create_task(run_every(reconcile_s, self.runtime_service.reconcile), name="reconcile"),
            asyncio.create_task(run_every(logs_s, self.runtime_log_service.ship), name="logs"),
        ]
        if self.health_service is not None:
            self._tasks.append(asyncio.create_task(run_every(telemetry_s, self.health_service.tick), name="health"))
        logger.info("Edge agent started for node %s", self.node_id)

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        try:
            await self.state_report_service.publish(NodeStatus.OFFLINE)
        except Exception:
            logger.warning("Could not publish OFFLINE state")
        await self._pubsub.disconnect()

    async def _on_runtime_status(self, instance: RuntimeInstance, status: RuntimeStatus) -> None:
        severity = Severity.ERROR if status == RuntimeStatus.FAILED else Severity.INFO
        kind = EventKind.ERROR if status == RuntimeStatus.FAILED else EventKind.RUNTIME
        if not self._pubsub.is_connected:
            return
        await self._publisher.event(
            kind,
            EdgeEvent(
                node_id=self.node_id,
                runtime_id=instance.runtime_id,
                severity=severity,
                event_type="runtime.status",
                message=f"{instance.spec.name} → {status.value}" + (f": {instance.message}" if instance.message else ""),
                data={"status": status.value, "container_id": instance.container_id},
            ),
        )

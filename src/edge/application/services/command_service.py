import logging
from collections import OrderedDict

from hopquangdo.messaging import Message
from pydantic import ValidationError

from src.edge.application.ports.edge_publisher import EdgePublisher
from src.edge.application.services.reporting import StateReportService
from src.edge.application.services.runtime_service import RuntimeService
from src.shared.contracts import (
    Command,
    CommandType,
    DeploymentEvent,
    DeploymentStatus,
    EventKind,
    RuntimeRef,
    RuntimeSpec,
    RuntimeStatus,
    Severity,
)
from src.shared.exceptions import AppException, ErrorCode

logger = logging.getLogger(__name__)

_LIFECYCLE = {CommandType.START, CommandType.STOP, CommandType.RESTART}


class CommandService:
    """Runs runtime commands, from the Cloud (MQTT) or the local API, and reports each result to the Cloud
    as a DeploymentEvent.
    """

    def __init__(
        self,
        node_id: str,
        runtime_service: RuntimeService,
        publisher: EdgePublisher,
        state_report_service: StateReportService,
        dedupe_size: int = 256,
    ) -> None:
        self._node_id = node_id
        self._runtime_service = runtime_service
        self._publisher = publisher
        self._state_report_service = state_report_service
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._dedupe_size = dedupe_size

    # --- Cloud commands (MQTT) ---
    async def handle(self, message: Message) -> None:
        try:
            command = Command.model_validate(message.payload_as_dict())
        except (ValidationError, ValueError) as exc:
            logger.warning("Rejected malformed command on %s: %s", message.topic, exc)
            return
        if self._already_seen(command.command_id):
            logger.info("Duplicate command %s ignored", command.command_id)
            return
        await self.execute(command)

    # --- local API ---
    async def deploy(self, spec: RuntimeSpec) -> DeploymentEvent:
        return await self.execute(Command(type=CommandType.DEPLOY, runtime=spec))

    async def update(self, runtime_id: str, spec: RuntimeSpec) -> DeploymentEvent:
        if spec.runtime_id != runtime_id:
            raise AppException(ErrorCode.INVALID_REQUEST, "runtime_id in body does not match path")
        self._runtime_service.get(runtime_id)
        return await self.execute(Command(type=CommandType.UPDATE, runtime=spec))

    async def remove(self, runtime_id: str) -> DeploymentEvent:
        self._runtime_service.get(runtime_id)
        return await self.execute(Command(type=CommandType.REMOVE, target=RuntimeRef(runtime_id=runtime_id)))

    async def control(self, runtime_id: str, action: CommandType) -> DeploymentEvent:
        if action not in _LIFECYCLE:
            raise AppException(ErrorCode.INVALID_REQUEST, f"Unsupported action {action}")
        self._runtime_service.get(runtime_id)
        return await self.execute(Command(type=action, target=RuntimeRef(runtime_id=runtime_id)))

    # --- execution ---
    async def execute(self, command: Command) -> DeploymentEvent:
        runtime_id = None
        try:
            runtime_id = command.runtime_id()
            status, runtime_status = await self._run(command, runtime_id)
            event = self._event(command, runtime_id, status, runtime_status, f"{command.type.value} succeeded")
        except AppException as exc:
            logger.warning("Command %s failed: %s", command.command_id, exc.message)
            runtime_status = None if exc.code == ErrorCode.NOT_FOUND else RuntimeStatus.FAILED
            event = self._event(command, runtime_id, DeploymentStatus.FAILED, runtime_status, exc.message, Severity.ERROR)
        except Exception as exc:
            logger.exception("Command %s failed", command.command_id)
            event = self._event(command, runtime_id, DeploymentStatus.FAILED, RuntimeStatus.FAILED, str(exc),
                                Severity.ERROR)
        await self._publisher.event(EventKind.DEPLOYMENT, event)
        await self._state_report_service.publish()
        return event

    async def _run(self, command: Command, runtime_id: str) -> tuple[DeploymentStatus, RuntimeStatus | None]:
        match command.type:
            case CommandType.DEPLOY | CommandType.UPDATE:
                if command.runtime is None:
                    raise AppException(ErrorCode.INVALID_REQUEST, f"{command.type.value} requires a runtime spec")
                instance = await self._runtime_service.apply(command.runtime)
            case CommandType.START:
                instance = await self._runtime_service.start(runtime_id)
            case CommandType.STOP:
                instance = await self._runtime_service.stop(runtime_id)
            case CommandType.RESTART:
                instance = await self._runtime_service.restart(runtime_id)
            case CommandType.REMOVE:
                await self._runtime_service.remove(runtime_id)
                return DeploymentStatus.REMOVED, RuntimeStatus.STOPPED
        return DeploymentStatus.SUCCEEDED, instance.status

    def _event(
        self,
        command: Command,
        runtime_id: str | None,
        status: DeploymentStatus,
        runtime_status: RuntimeStatus | None,
        message: str,
        severity: Severity = Severity.INFO,
    ) -> DeploymentEvent:
        return DeploymentEvent(
            node_id=self._node_id,
            severity=severity,
            event_type=f"command.{command.type.value}",
            message=message,
            runtime_id=runtime_id,
            command_id=command.command_id,
            deployment_id=command.deployment_id,
            status=status,
            runtime_status=runtime_status,
        )

    def _already_seen(self, command_id: str) -> bool:
        if command_id in self._seen:
            return True
        self._seen[command_id] = None
        if len(self._seen) > self._dedupe_size:
            self._seen.popitem(last=False)
        return False

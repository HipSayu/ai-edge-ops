import logging

from hopquangdo.messaging import Message

from src.cloud.application.ports.deployment_repository import DeploymentRepository
from src.cloud.application.ports.runtime_repository import RuntimeRepository
from src.shared.contracts import DeploymentEvent, DeploymentStatus

logger = logging.getLogger(__name__)


class DeploymentEventHandler:
    """Consumes `edge/+/+/event/deployment` and closes the loop on deployments."""

    def __init__(self, deployments: DeploymentRepository, runtimes: RuntimeRepository) -> None:
        self._deployments = deployments
        self._runtimes = runtimes

    async def handle(self, message: Message) -> None:
        event = DeploymentEvent.model_validate(message.payload_as_dict())
        deployment = None
        if event.deployment_id:
            deployment = await self._deployments.get(event.deployment_id)
        if deployment is None and event.runtime_id:
            deployment = await self._deployments.get_by_runtime(event.runtime_id)
        if deployment is None:
            logger.warning("Deployment event %s matches no deployment", event.event_id)
            return

        if not deployment.apply_result(event.command_id, event.status, event.message):
            logger.info("Ignoring stale result for command %s", event.command_id)
            return
        await self._deployments.save(deployment)

        if event.status == DeploymentStatus.REMOVED:
            await self._runtimes.delete(deployment.runtime_id)
        elif event.runtime_status is not None:
            await self._runtimes.update_status(deployment.runtime_id, event.runtime_status)

import logging

from hopquangdo.messaging import Message

from src.cloud.application.ports.node_repository import NodeRepository
from src.cloud.application.ports.runtime_repository import RuntimeRepository
from src.cloud.domain.value_objects.node_heartbeat import NodeHeartbeat
from src.shared.contracts import EdgeTopics, NodeState

logger = logging.getLogger(__name__)


class NodeStateHandler:
    """Consumes `edge/+/+/state` and records the node's reported state and runtime statuses."""

    def __init__(self, nodes: NodeRepository, runtimes: RuntimeRepository) -> None:
        self._nodes = nodes
        self._runtimes = runtimes

    async def handle(self, message: Message) -> None:
        address = EdgeTopics.parse(message.topic)
        if address.kind is not None:
            return
        state = NodeState.model_validate(message.payload_as_dict())
        if await self._nodes.get(state.node_id) is None:
            logger.warning("State from unregistered node %s (cluster %s)", state.node_id, address.cluster_id)
            return
        await self._nodes.apply_heartbeat(
            NodeHeartbeat(
                node_id=state.node_id,
                status=state.agent_status,
                at=state.timestamp,
                agent_version=state.agent_version,
                hostname=state.hostname,
                ip_address=state.ip_address,
                cpu_cores=state.cpu_cores,
                memory_total_mb=state.memory_total_mb,
                gpu_name=state.gpu_name,
            )
        )
        for reported in state.runtimes:
            runtime = await self._runtimes.get(reported.runtime_id)
            if runtime is None or runtime.node_id != state.node_id:
                continue
            if runtime.status != reported.status or runtime.container_id != reported.container_id:
                await self._runtimes.update_status(runtime.id, reported.status, reported.container_id)

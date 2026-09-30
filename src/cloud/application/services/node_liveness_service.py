import logging
from datetime import timedelta

from src.cloud.application.ports.node_repository import NodeRepository
from src.shared.application.periodic import run_every
from src.shared.domain.clock import Clock

logger = logging.getLogger(__name__)


class NodeLivenessService:
    """Marks nodes OFFLINE when their heartbeat is older than `timeout_sec`."""

    def __init__(self, nodes: NodeRepository, timeout_sec: float, interval_sec: float = 10.0) -> None:
        self._nodes = nodes
        self._timeout = timedelta(seconds=timeout_sec)
        self._interval = interval_sec

    async def sweep(self) -> list[str]:
        stale = await self._nodes.mark_offline_before(Clock.now() - self._timeout)
        for node_id in stale:
            logger.warning("Node %s heartbeat expired, marked OFFLINE", node_id)
        return stale

    async def run(self) -> None:
        await run_every(self._interval, self.sweep, immediately=True)

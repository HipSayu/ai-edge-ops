from dataclasses import dataclass
from datetime import datetime

from src.shared.contracts import NodeStatus


@dataclass(frozen=True, slots=True)
class NodeHeartbeat:
    """Reported facts about a node extracted from its NodeState message."""

    node_id: str
    status: NodeStatus
    at: datetime
    agent_version: str | None = None
    hostname: str | None = None
    ip_address: str | None = None
    cpu_cores: int | None = None
    memory_total_mb: int | None = None
    gpu_name: str | None = None

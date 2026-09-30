from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.shared.contracts import NodeStatus


@dataclass(slots=True)
class Node:
    id: str
    cluster_id: str
    name: str
    hostname: str | None = None
    ip_address: str | None = None
    status: NodeStatus = NodeStatus.UNKNOWN
    agent_version: str | None = None
    cpu_cores: int | None = None
    memory_total_mb: int | None = None
    gpu_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    last_heartbeat_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

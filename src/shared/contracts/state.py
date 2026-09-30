from datetime import datetime

from pydantic import BaseModel, Field

from src.shared.contracts.enums import NodeStatus, RuntimeStatus
from src.shared.domain.clock import Clock


class RuntimeState(BaseModel):
    runtime_id: str
    name: str
    status: RuntimeStatus
    image: str | None = None
    container_id: str | None = None
    restart_count: int = 0
    started_at: datetime | None = None
    message: str | None = None


class NodeState(BaseModel):
    """Retained message on `edge/{cluster}/{node}/state` — the node's reported (actual) state."""

    cluster_id: str
    node_id: str
    agent_status: NodeStatus
    agent_version: str
    hostname: str | None = None
    ip_address: str | None = None
    cpu_cores: int | None = None
    memory_total_mb: int | None = None
    gpu_name: str | None = None
    runtimes: list[RuntimeState] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=Clock.now)

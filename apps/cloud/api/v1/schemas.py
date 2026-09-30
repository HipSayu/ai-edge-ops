"""Request/response models of the Cloud REST API v1 (docs/api/Readme.md §3)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.shared.contracts import (
    ClusterStatus,
    DeploymentStatus,
    NodeStatus,
    RuntimeStatus,
    RuntimeType,
)


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ClusterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    location: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClusterOut(_Out):
    id: str
    name: str
    description: str | None
    status: ClusterStatus
    location: str | None
    metadata: dict[str, Any]
    created_at: datetime | None
    updated_at: datetime | None


class ClusterUpdate(BaseModel):
    """Only the fields sent are changed."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    location: str | None = None
    metadata: dict[str, Any] | None = None


class NodeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    metadata: dict[str, Any] | None = None


class NodeCreate(BaseModel):
    cluster_id: str
    name: str = Field(min_length=1, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NodeOut(_Out):
    id: str
    cluster_id: str
    name: str
    hostname: str | None
    ip_address: str | None
    status: NodeStatus
    agent_version: str | None
    cpu_cores: int | None
    memory_total_mb: int | None
    gpu_name: str | None
    metadata: dict[str, Any]
    last_heartbeat_at: datetime | None
    created_at: datetime | None


class RuntimeOut(_Out):
    id: str
    node_id: str
    name: str
    type: RuntimeType
    status: RuntimeStatus
    image_uri: str | None
    image_tag: str | None
    model_id: str | None
    config: dict[str, Any]
    container_id: str | None
    started_at: datetime | None
    stopped_at: datetime | None


class AgentOut(BaseModel):
    node_id: str
    cluster_id: str
    status: NodeStatus
    agent_version: str | None
    last_heartbeat_at: datetime | None
    runtimes: list[RuntimeOut]


class RuntimeLogOut(BaseModel):
    node_id: str
    runtime_id: str
    runtime_name: str
    timestamp: datetime
    level: str
    message: str


class DeploymentOut(_Out):
    id: str
    cluster_id: str
    node_id: str
    runtime_id: str
    spec: dict[str, Any]
    status: DeploymentStatus
    last_command_id: str | None
    message: str | None
    created_at: datetime | None
    updated_at: datetime | None

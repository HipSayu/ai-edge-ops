import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.shared.contracts.enums import DeploymentStatus, RuntimeStatus, Severity
from src.shared.domain.clock import Clock


class EdgeEvent(BaseModel):
    """Published on `edge/{cluster}/{node}/event/{kind}`."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str
    severity: Severity = Severity.INFO
    event_type: str
    message: str
    runtime_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=Clock.now)


class DeploymentEvent(EdgeEvent):
    """Result of executing a command — lets the Cloud close the loop on a deployment."""

    command_id: str
    deployment_id: str | None = None
    status: DeploymentStatus
    runtime_status: RuntimeStatus | None = None

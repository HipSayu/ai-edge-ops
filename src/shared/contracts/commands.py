import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from src.shared.contracts.enums import RuntimeType
from src.shared.domain.clock import Clock


class CommandType(StrEnum):
    DEPLOY = "deploy"
    UPDATE = "update"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    REMOVE = "remove"


class RuntimeSpec(BaseModel):
    """Desired state of one AI Runtime on a node. Deploy/update are idempotent on `runtime_id`."""

    runtime_id: str
    name: str
    type: RuntimeType = RuntimeType.VISION
    image_uri: str
    image_tag: str = "latest"
    model_id: str | None = None
    model_uri: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, str] = Field(default_factory=dict)
    resource_limits: dict[str, Any] = Field(default_factory=dict)

    @property
    def image(self) -> str:
        return f"{self.image_uri}:{self.image_tag}"


class RuntimeRef(BaseModel):
    runtime_id: str


class Command(BaseModel):
    """Envelope published on `edge/{cluster}/{node}/command/{type}`."""

    command_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: CommandType
    deployment_id: str | None = None
    issued_at: datetime = Field(default_factory=Clock.now)
    runtime: RuntimeSpec | None = None
    target: RuntimeRef | None = None

    def runtime_id(self) -> str:
        if self.runtime is not None:
            return self.runtime.runtime_id
        if self.target is not None:
            return self.target.runtime_id
        raise ValueError(f"Command {self.command_id} has no runtime target")

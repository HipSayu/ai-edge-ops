from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.shared.contracts import DeploymentStatus, RuntimeStatus, Severity


class CommandResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    command_id: str
    status: DeploymentStatus
    runtime_id: str | None
    runtime_status: RuntimeStatus | None
    message: str


class RuntimeEventIn(BaseModel):
    event_type: str
    message: str
    severity: Severity = Severity.INFO
    data: dict[str, Any] = Field(default_factory=dict)


class AcceptedOut(BaseModel):
    accepted: bool = True

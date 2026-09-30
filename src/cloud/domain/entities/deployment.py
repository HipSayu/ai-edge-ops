from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.shared.contracts import DeploymentStatus, RuntimeSpec
from src.shared.exceptions import AppException, ErrorCode

_TERMINAL = {DeploymentStatus.REMOVED}


@dataclass(slots=True)
class Deployment:
    """Desired state of one runtime on one node, and the progress of reconciling it."""

    id: str
    cluster_id: str
    node_id: str
    runtime_id: str
    spec: dict[str, Any]
    status: DeploymentStatus = DeploymentStatus.PENDING
    last_command_id: str | None = None
    message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def runtime_spec(self) -> RuntimeSpec:
        return RuntimeSpec.model_validate(self.spec)

    def is_removed(self) -> bool:
        return self.status in _TERMINAL

    def dispatched(self, command_id: str, status: DeploymentStatus = DeploymentStatus.IN_PROGRESS) -> None:
        if self.is_removed():
            raise AppException(ErrorCode.CONFLICT, f"Deployment {self.id} is removed")
        self.last_command_id = command_id
        self.status = status
        self.message = None

    def apply_result(self, command_id: str, status: DeploymentStatus, message: str | None) -> bool:
        """Apply an edge-reported result. Results for superseded commands are ignored."""
        if self.is_removed() or command_id != self.last_command_id:
            return False
        self.status = status
        self.message = message
        return True

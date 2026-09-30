from dataclasses import dataclass
from datetime import datetime

from src.shared.contracts import RuntimeSpec, RuntimeState, RuntimeStatus


@dataclass(slots=True)
class RuntimeInstance:
    """Desired spec + observed status of one AI Runtime on this node."""

    spec: RuntimeSpec
    desired_running: bool = True
    status: RuntimeStatus = RuntimeStatus.CREATING
    container_id: str | None = None
    restart_count: int = 0
    started_at: datetime | None = None
    message: str | None = None

    @property
    def runtime_id(self) -> str:
        return self.spec.runtime_id

    def to_state(self) -> RuntimeState:
        return RuntimeState(
            runtime_id=self.runtime_id,
            name=self.spec.name,
            status=self.status,
            image=self.spec.image,
            container_id=self.container_id,
            restart_count=self.restart_count,
            started_at=self.started_at,
            message=self.message,
        )

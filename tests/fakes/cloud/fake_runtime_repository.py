from __future__ import annotations

from src.cloud.domain.entities.runtime import Runtime
from src.shared.contracts import RuntimeStatus
from src.shared.domain.clock import Clock


class FakeRuntimeRepository:
    def __init__(self) -> None:
        self._items: dict[str, Runtime] = {}

    async def add(self, runtime: Runtime) -> Runtime:
        runtime.created_at = runtime.updated_at = Clock.now()
        self._items[runtime.id] = runtime
        return runtime

    async def get(self, runtime_id: str) -> Runtime | None:
        return self._items.get(runtime_id)

    async def list(self, node_id: str | None = None) -> list[Runtime]:
        return [r for r in self._items.values() if node_id is None or r.node_id == node_id]

    async def save(self, runtime: Runtime) -> None:
        runtime.updated_at = Clock.now()
        self._items[runtime.id] = runtime

    async def update_status(self, runtime_id: str, status: RuntimeStatus, container_id: str | None = None) -> None:
        runtime = self._items.get(runtime_id)
        if runtime is None:
            return
        if status == RuntimeStatus.RUNNING and runtime.status != RuntimeStatus.RUNNING:
            runtime.started_at = Clock.now()
        if status in (RuntimeStatus.STOPPED, RuntimeStatus.FAILED):
            runtime.stopped_at = Clock.now()
        runtime.status = status
        runtime.container_id = container_id or runtime.container_id
        runtime.updated_at = Clock.now()

    async def delete(self, runtime_id: str) -> None:
        self._items.pop(runtime_id, None)

from __future__ import annotations

from typing import Protocol

from src.cloud.domain.entities.runtime import Runtime
from src.shared.contracts import RuntimeStatus


class RuntimeRepository(Protocol):
    async def add(self, runtime: Runtime) -> Runtime: ...

    async def get(self, runtime_id: str) -> Runtime | None: ...

    async def list(self, node_id: str | None = None) -> list[Runtime]: ...

    async def save(self, runtime: Runtime) -> None: ...

    async def update_status(
        self, runtime_id: str, status: RuntimeStatus, container_id: str | None = None
    ) -> None: ...

    async def delete(self, runtime_id: str) -> None: ...

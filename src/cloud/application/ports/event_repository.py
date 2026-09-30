from __future__ import annotations

from typing import Any, Protocol

from src.shared.contracts import EdgeEvent


class EventRepository(Protocol):
    async def append(self, event: EdgeEvent) -> None: ...

    async def list(self, node_id: str, limit: int = 100) -> list[dict[str, Any]]: ...

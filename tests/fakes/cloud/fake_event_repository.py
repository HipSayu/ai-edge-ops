from __future__ import annotations

from typing import Any

from src.shared.contracts import EdgeEvent


class FakeEventRepository:
    def __init__(self) -> None:
        self._events: list[EdgeEvent] = []

    async def append(self, event: EdgeEvent) -> None:
        self._events.append(event)

    async def list(self, node_id: str, limit: int = 100) -> list[dict[str, Any]]:
        matches = [e for e in reversed(self._events) if e.node_id == node_id]
        return [e.model_dump(mode="json") for e in matches[:limit]]

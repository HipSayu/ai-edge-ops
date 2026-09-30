from typing import Any

from src.shared.contracts import RuntimeLogBatch


class FakeRuntimeLogRepository:
    def __init__(self) -> None:
        self._lines: dict[str, list[dict[str, Any]]] = {}

    async def append(self, batch: RuntimeLogBatch) -> None:
        self._lines.setdefault(batch.runtime_id, []).extend(
            {"node_id": batch.node_id, "runtime_id": batch.runtime_id, "runtime_name": batch.runtime_name,
             **line.model_dump(mode="json")}
            for line in batch.lines
        )

    async def recent(self, runtime_id: str, limit: int = 200) -> list[dict[str, Any]]:
        return self._lines.get(runtime_id, [])[-limit:]

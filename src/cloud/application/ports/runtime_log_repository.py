from typing import Any, Protocol

from src.shared.contracts import RuntimeLogBatch


class RuntimeLogRepository(Protocol):
    """Recent container log lines per runtime (hot, bounded; not an archive)."""

    async def append(self, batch: RuntimeLogBatch) -> None: ...

    async def recent(self, runtime_id: str, limit: int = 200) -> list[dict[str, Any]]:
        """Newest `limit` lines, oldest first."""
        ...

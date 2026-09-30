from typing import Any, Protocol


class TelemetryRepository(Protocol):
    """Hot telemetry: latest sample per (node, kind[, runtime]) plus a bounded recent history."""

    async def record(self, node_id: str, kind: str, key: str, sample: dict[str, Any]) -> None: ...

    async def latest(self, node_id: str) -> dict[str, dict[str, Any]]:
        """Map of `kind` or `kind:runtime_id` -> latest sample."""
        ...

    async def history(self, node_id: str, kind: str, limit: int = 100) -> list[dict[str, Any]]: ...

    async def ping(self) -> bool: ...

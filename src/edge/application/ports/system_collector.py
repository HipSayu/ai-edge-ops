from typing import Protocol

from src.shared.contracts import SystemTelemetry


class SystemCollector(Protocol):
    async def collect(self, node_id: str) -> SystemTelemetry: ...

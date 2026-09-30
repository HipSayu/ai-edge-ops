from typing import Protocol

from src.shared.contracts import GpuTelemetry


class GpuCollector(Protocol):
    async def collect(self, node_id: str) -> GpuTelemetry | None:
        """None when the node has no supported accelerator."""
        ...

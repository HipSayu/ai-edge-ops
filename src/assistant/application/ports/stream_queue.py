from collections.abc import AsyncIterator
from typing import Protocol


class StreamQueue(Protocol):
    """SSE frame buffer between the producer task and exactly one consumer of a chat stream."""

    async def open(self, stream_id: str) -> None: ...

    async def put(self, stream_id: str, frame: str) -> None: ...

    async def close(self, stream_id: str) -> None:
        """Marks the end of the stream; the consumer stops after draining."""
        ...

    async def ping(self) -> bool: ...

    async def subscribe(self, stream_id: str) -> AsyncIterator[str] | None:
        """Claims the stream for one consumer; None if unknown, expired or already claimed."""
        ...

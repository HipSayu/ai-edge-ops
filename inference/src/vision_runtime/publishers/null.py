"""No-op publisher — for tests and devices with streaming disabled."""

from __future__ import annotations

from vision_runtime.publishers.base import VideoPublisher


class NullPublisher(VideoPublisher):
    def __init__(self) -> None:
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    async def start(self, *, source: str, whip_url: str, token: str, loop: bool = False) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False


__all__ = ["NullPublisher"]

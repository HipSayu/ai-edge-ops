"""Minimal in-process domain event bus.

Modules publish dataclass events after committing their own transaction; subscribers
react in their own session. Swap this for Redis/NATS later without touching call sites.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

Event = TypeVar("Event")
Handler = Callable[[Any], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: type[Event], handler: Callable[[Event], Awaitable[None]]) -> None:
        self._handlers[event_type].append(handler)  # type: ignore[arg-type]

    async def publish(self, event: object) -> None:
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception:  # noqa: BLE001 - one bad subscriber must not break the publisher
                logger.exception("event handler %s failed for %s", handler, type(event).__name__)

    def clear(self) -> None:
        """Test helper."""
        self._handlers.clear()


event_bus = EventBus()

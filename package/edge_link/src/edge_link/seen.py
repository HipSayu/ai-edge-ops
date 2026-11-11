"""Which events a subscriber has already taken, so a redelivery (QoS 1 is at least once) is dropped.

The subscriber only needs this contract. In memory it covers one process; a shared store (Redis) lets several cloud
instances, or a restarted one, agree on what was taken."""

from collections import OrderedDict
from typing import Protocol

_REMEMBERED = 10_000


class SeenEvents(Protocol):
    def claim(self, event_id: str) -> bool:
        """True for the first caller of an id, False for everyone after (until it is released)."""

    def release(self, event_id: str) -> None:
        """Forgets an id, so the event can be taken again (its handler failed)."""


class MemorySeen:
    def __init__(self, remembered: int = _REMEMBERED) -> None:
        self._ids: OrderedDict[str, None] = OrderedDict()
        self._remembered = remembered

    def claim(self, event_id: str) -> bool:
        if event_id in self._ids:
            return False
        self._ids[event_id] = None
        if len(self._ids) > self._remembered:
            self._ids.popitem(last=False)
        return True

    def release(self, event_id: str) -> None:
        self._ids.pop(event_id, None)

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass

from dqh.svc_core.helpers.time import utcnow

from app.domain.presence.models import PresenceEvent, PresenceSnapshot, PresenceStatus

Clock = Callable[[], dt.datetime]


@dataclass
class _Entry:
    status: PresenceStatus
    last_seen_at: dt.datetime | None
    since: dt.datetime


class PresenceRegistry:
    """Track endpoint liveness using online, stale, and offline states."""

    def __init__(self, *, stale_after: float = 45.0, offline_after: float = 90.0, clock: Clock = utcnow) -> None:
        if stale_after >= offline_after:
            raise ValueError("stale_after must be < offline_after")
        self._stale = stale_after
        self._offline = offline_after
        self._clock = clock
        self._entries: dict[str, _Entry] = {}

    def mark_seen(self, endpoint_id: str, *, at: dt.datetime | None = None) -> PresenceEvent | None:
        now = at or self._clock()
        entry = self._entries.get(endpoint_id)
        previous = entry.status if entry else None
        if entry is None:
            self._entries[endpoint_id] = _Entry(PresenceStatus.ONLINE, now, now)
        else:
            entry.last_seen_at = now
            if entry.status is not PresenceStatus.ONLINE:
                entry.status = PresenceStatus.ONLINE
                entry.since = now
        return PresenceEvent(endpoint_id, previous, PresenceStatus.ONLINE, now) if previous is not PresenceStatus.ONLINE else None

    def mark_offline(self, endpoint_id: str, *, at: dt.datetime | None = None) -> PresenceEvent | None:
        now = at or self._clock()
        entry = self._entries.get(endpoint_id)
        previous = entry.status if entry else None
        if entry is None:
            self._entries[endpoint_id] = _Entry(PresenceStatus.OFFLINE, None, now)
        elif entry.status is not PresenceStatus.OFFLINE:
            entry.status = PresenceStatus.OFFLINE
            entry.since = now
        return PresenceEvent(endpoint_id, previous, PresenceStatus.OFFLINE, now) if previous is not PresenceStatus.OFFLINE else None

    def forget(self, endpoint_id: str) -> None:
        self._entries.pop(endpoint_id, None)

    def evaluate(self, *, at: dt.datetime | None = None) -> list[PresenceEvent]:
        now = at or self._clock()
        events: list[PresenceEvent] = []
        for endpoint_id, entry in self._entries.items():
            if entry.last_seen_at is None:
                continue
            elapsed = (now - entry.last_seen_at).total_seconds()
            target = PresenceStatus.OFFLINE if elapsed >= self._offline else PresenceStatus.STALE if elapsed >= self._stale else PresenceStatus.ONLINE
            if target is not entry.status:
                events.append(PresenceEvent(endpoint_id, entry.status, target, now))
                entry.status = target
                entry.since = now
        return events

    def status(self, endpoint_id: str) -> PresenceStatus | None:
        entry = self._entries.get(endpoint_id)
        return entry.status if entry else None

    def snapshot(self) -> list[PresenceSnapshot]:
        return [PresenceSnapshot(eid, entry.status, entry.last_seen_at, entry.since) for eid, entry in self._entries.items()]


__all__ = ["PresenceRegistry", "Clock"]
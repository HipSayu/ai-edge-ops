"""Value objects emitted by :class:`PresenceRegistry`."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from app.modules.agent.presence_status import PresenceStatus


@dataclass(frozen=True)
class PresenceSnapshot:
    endpoint_id: str
    status: PresenceStatus
    last_seen_at: dt.datetime | None
    since: dt.datetime


@dataclass(frozen=True)
class PresenceEvent:
    endpoint_id: str
    previous: PresenceStatus | None
    current: PresenceStatus
    at: dt.datetime


__all__ = ["PresenceEvent", "PresenceSnapshot"]

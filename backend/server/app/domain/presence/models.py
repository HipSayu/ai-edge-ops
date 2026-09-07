from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from enum import Enum


class PresenceStatus(str, Enum):
    ONLINE = "online"
    STALE = "stale"
    OFFLINE = "offline"

    def __str__(self) -> str:
        return self.value


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


__all__ = ["PresenceStatus", "PresenceSnapshot", "PresenceEvent"]
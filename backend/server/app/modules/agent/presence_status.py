"""Liveness state of an endpoint tracked by :class:`PresenceRegistry`."""

from __future__ import annotations

from dqh.svc_core.helpers.str_enum import StrEnum


class PresenceStatus(StrEnum):
    ONLINE = "online"
    STALE = "stale"
    OFFLINE = "offline"


__all__ = ["PresenceStatus"]

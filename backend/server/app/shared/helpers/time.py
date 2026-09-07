"""Application time helpers."""

from __future__ import annotations

import datetime as dt


def utcnow() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)


__all__ = ["utcnow"]
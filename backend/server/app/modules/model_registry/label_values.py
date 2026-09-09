"""Coerce OCI image-label string values — labels are always strings."""

from __future__ import annotations

import datetime as dt


def parse_datetime(raw: str | None) -> dt.datetime | None:
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def split_csv(raw: str | None) -> list[str]:
    return [p.strip() for p in raw.split(",") if p.strip()] if raw else []


def to_float(raw: str | None) -> float | None:
    try:
        return float(raw) if raw not in (None, "") else None
    except (TypeError, ValueError):
        return None


__all__ = ["parse_datetime", "split_csv", "to_float"]

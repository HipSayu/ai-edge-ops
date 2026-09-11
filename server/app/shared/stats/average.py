"""Mean of a list, or ``None`` when empty."""

from __future__ import annotations


def average_or_none(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


__all__ = ["average_or_none"]

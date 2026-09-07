"""Enum helpers shared by application domains."""

from __future__ import annotations

import enum


class StrEnum(str, enum.Enum):
    def __str__(self) -> str:
        return self.value


__all__ = ["StrEnum"]
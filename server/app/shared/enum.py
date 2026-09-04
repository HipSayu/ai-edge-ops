"""Helpers for string-backed enums stored as VARCHAR (portable across databases)."""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum


class StrEnum(str, enum.Enum):
    def __str__(self) -> str:  # noqa: D105
        return self.value


def db_enum(enum_cls: type[enum.Enum], *, length: int = 32) -> SAEnum:
    """Column type: store the enum *value* as a string, no native DB enum."""
    return SAEnum(enum_cls, native_enum=False, length=length, values_callable=lambda e: [m.value for m in e])

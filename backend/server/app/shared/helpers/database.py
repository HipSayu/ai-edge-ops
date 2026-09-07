"""Database mapping helpers."""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum


def db_enum(enum_cls: type[enum.Enum], *, length: int = 32) -> SAEnum:
    """Store a Python enum value as a portable VARCHAR-backed database enum."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        values_callable=lambda members: [member.value for member in members],
    )


__all__ = ["db_enum"]
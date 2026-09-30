import uuid
from dataclasses import fields
from typing import Any, TypeVar

T = TypeVar("T")


class RowMapper:
    """Maps an asyncpg Record onto a dataclass, stringifying UUID/INET columns."""

    @staticmethod
    def _normalize(value: Any) -> Any:
        if isinstance(value, uuid.UUID):
            return str(value)
        if value is not None and type(value).__module__ == "ipaddress":
            return str(value)
        return value

    @classmethod
    def to(cls, target: type[T], row: Any) -> T:
        names = {f.name for f in fields(target)}  # type: ignore[arg-type]
        return target(**{k: cls._normalize(v) for k, v in dict(row).items() if k in names})

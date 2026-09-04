"""Generic pagination primitives shared by every list endpoint."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    limit: int
    offset: int

    @classmethod
    def build(cls, items: Sequence[T], total: int, params: PageParams) -> Page[T]:
        return cls(items=items, total=total, limit=params.limit, offset=params.offset)

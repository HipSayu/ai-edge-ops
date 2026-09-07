"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from dqh.svc_core.transports.http.fastapi import Pagination as Pagination
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]

__all__ = ["DbSession", "Pagination"]

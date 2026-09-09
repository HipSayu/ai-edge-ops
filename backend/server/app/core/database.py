"""Async SQLAlchemy engine/session wiring.

The engine is built from ``settings.db`` via
:class:`dqh.svc_core.persistence.sqlalchemy.EngineFactory`; ``Base`` and the
repository base also come from svc_core. Schema is created on startup via
:func:`init_db` (swap for Alembic later — the ``alembic/`` layout is in place).

``async_session`` is a module global on purpose: tests swap it (and ``engine``)
for a SQLite factory, and :func:`session_scope` / :func:`get_db` read it at call
time.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dqh.svc_core.persistence.sqlalchemy import Base, EngineFactory
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings

engine = EngineFactory(settings.db).create()
async_session = async_sessionmaker(engine, expire_on_commit=False)

__all__ = ["Base", "async_session", "engine", "get_db", "init_db", "session_scope"]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one session per request, rolled back on error."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Standalone session for event handlers / workers (not request-scoped)."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create any missing tables. Importing ``app.modules`` registers every ORM model."""
    import app.modules  # noqa: F401  (side-effect: populates Base.metadata)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

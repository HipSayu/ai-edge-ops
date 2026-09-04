"""Async SQLAlchemy engine/session setup.

Production uses PostgreSQL (asyncpg). Schema is created on startup via ``init_db``
(swap for Alembic migrations later — the ``alembic/`` layout is left in place).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.db.url,
    echo=settings.db.echo,
    pool_pre_ping=settings.db.pool_pre_ping,
    pool_recycle=settings.db.pool_recycle_s,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


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
    """Standalone session for event handlers / workers (not request-scoped).

    Reads the module-level ``async_session`` at call time so tests can swap it.
    """
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

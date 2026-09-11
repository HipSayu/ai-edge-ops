"""Test harness: in-memory SQLite shared across the app + event handlers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.core.database as database
import app.modules as modules  # noqa: F401  (registers ORM models)
from app.api.deps import get_db
from app.core.database import Base
from app.core.events import event_bus
from app.core.ws import ws_hub
from app.main import create_app
from app.modules import register_event_handlers, reset_event_handlers
from app.modules.agent import telemetry_relay as agent_ws_relay


@pytest_asyncio.fixture
async def _engine() -> AsyncGenerator[object, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    prev_engine, prev_factory = database.engine, database.async_session
    database.engine = engine
    database.async_session = async_sessionmaker(engine, expire_on_commit=False)

    event_bus.clear()
    agent_ws_relay.reset_cache()
    reset_event_handlers()
    register_event_handlers()
    if not ws_hub.connected:
        await ws_hub.connect()

    yield engine

    database.engine, database.async_session = prev_engine, prev_factory
    event_bus.clear()
    agent_ws_relay.reset_cache()
    reset_event_handlers()
    await ws_hub.aclose()
    await engine.dispose()


@pytest_asyncio.fixture
async def session(_engine) -> AsyncGenerator[AsyncSession, None]:
    async with database.async_session() as s:
        yield s


@pytest_asyncio.fixture
async def client(_engine) -> AsyncGenerator[AsyncClient, None]:
    fastapi_app = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with database.async_session() as s:
            yield s

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=fastapi_app)
    # trailing slash + relative request paths so httpx keeps the /api/v1 prefix
    async with AsyncClient(transport=transport, base_url="http://test/api/v1/") as c:
        yield c

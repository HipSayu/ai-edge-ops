"""FastAPI entrypoint for the AI Edge Ops platform API.

Run (from app/backend/): uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from dqh.svc_core.http.adapters.fastapi import create_app as svc_create_app
from fastapi import FastAPI
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_db, session_scope
from app.core.logging import configure_logging
from app.edge.runtime import EdgePlane
from app.modules import register_event_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    register_event_handlers()
    await init_db()
    edge = EdgePlane()
    await edge.start()
    app.state.edge = edge
    try:
        yield
    finally:
        await edge.stop()


async def _db_check() -> bool:
    async with session_scope() as session:
        await session.execute(text("SELECT 1"))
    return True


def create_app() -> FastAPI:
    return svc_create_app(
        title=settings.app_name,
        version="0.1.0",
        routers=[api_router],
        router_prefix=settings.api_v1_prefix,
        cors_origins=settings.cors_origins,
        lifespan=lifespan,
        health_path=f"{settings.api_v1_prefix}/health",
        health_checks={"db": _db_check},
    )


app = create_app()

"""FastAPI entrypoint for the AI Edge Ops platform API.

Run (from app/): uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from dqh.svc_core.middleware.logging import configure_logging
from dqh.svc_core.transports.http.fastapi import create_app as svc_create_app
from fastapi import FastAPI
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_db, session_scope
from app.core.ws import ws_hub
from app.edge.runtime import EdgePlane
from app.modules import register_event_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    if settings.environment == "production" and (
        settings.jwt_secret == "change-this-in-production" or len(settings.jwt_secret) < 32
    ):
        raise RuntimeError("JWT_SECRET must be a random value of at least 32 characters in production")
    register_event_handlers()
    await init_db()
    await ws_hub.connect()
    edge = EdgePlane()
    await edge.start()
    app.state.edge = edge
    try:
        yield
    finally:
        await edge.stop()
        await ws_hub.aclose()


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

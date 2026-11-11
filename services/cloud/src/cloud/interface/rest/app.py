"""Builds the cloud interface: REST, MCP, and the lifespan that starts the container. main.py only runs the result."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from cloud.interface.mcp import build_mcp
from cloud.interface.mcp.runner import bind_container
from cloud.interface.rest.routers import router as api
from cloud.bootstrap.container import build_container
from cloud.bootstrap.settings import Settings
from trace_id import RequestLogMiddleware
from shared.http import register_error_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    mcp = build_mcp()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        container = build_container(settings)
        app.state.container = container
        container.start()
        async with mcp.session_manager.run():
            yield
        container.shutdown()

    app = FastAPI(title="Cloud API", lifespan=lifespan)
    bind_container(lambda: app.state.container)
    register_error_handlers(app)
    app.add_middleware(RequestLogMiddleware, service="cloud")
    app.include_router(api)
    app.mount("/", mcp.streamable_http_app())  # last: /api and /health match first, /mcp falls through to here
    return app

"""Standalone ASGI entrypoint for the MCP server (its own process).

    uvicorn app.mcp_main:app --port 8001

Same `app` packages, same DB / config as the REST server — but it mounts only
``/mcp`` (+ ``/health``), no REST routers, no edge MQTT gateway.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from dqh.svc_core.middleware.logging import configure_logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.database import init_db, session_scope
from app.mcp.server import build_asgi_app
from app.modules import register_event_handlers
from app.modules.iam.bearer_auth import bearer_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    register_event_handlers()  # tools read models; keep metadata consistent
    await init_db()
    mcp_app = build_asgi_app()
    async with mcp_app.router.lifespan_context(mcp_app):
        app.mount("/mcp", mcp_app)
        yield


class _McpAuthMiddleware(BaseHTTPMiddleware):
    """Bearer-token gate on /mcp — same JWTs as the REST API. Open in local env."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp") and settings.environment != "local":
            header = request.headers.get("authorization", "")
            token = header[7:] if header.lower().startswith("bearer ") else None
            if not token:
                return JSONResponse({"detail": "authentication required"}, status_code=401)
            try:
                from app.core.token_codec import decode_token

                async with session_scope() as session:
                    from app.modules.iam.models import User

                    user = await session.get(User, decode_token(token, "access"))
                if user is None or not user.active:
                    return JSONResponse({"detail": "invalid token"}, status_code=401)
            except Exception:  # noqa: BLE001
                return JSONResponse({"detail": "invalid token"}, status_code=401)
        return await call_next(request)


def create_app() -> FastAPI:
    app = FastAPI(title="AI Edge Ops MCP", version="0.1.0", lifespan=lifespan)
    app.add_middleware(_McpAuthMiddleware)

    @app.get("/health")
    async def health() -> dict:
        async with session_scope() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()

# `bearer_auth` imported to keep the auth surface obvious; used above lazily.
_ = bearer_auth

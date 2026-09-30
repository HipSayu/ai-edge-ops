"""Cloud: the single entrypoint. REST /api/v1, WebSocket /api/v1/ws, MCP /mcp and the MQTT worker on one port.

Run: python -m apps.cloud.main   (from repo root)
  CLOUD_EMBEDDED_WORKER=true   also consume edge state/telemetry/events + sweep liveness (default here)
Needs Postgres, Redis and the MQTT broker (infra/compose/cloud).
"""

import asyncio
import contextlib
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from hopquangdo.http import ServiceApp, ServiceRunner
from hopquangdo.observability import LoggingSetup

from apps.cloud import dependencies
from apps.cloud.access_log_redactor import AccessLogRedactor
from apps.cloud.api.v1 import (
    agent_router,
    auth_router,
    cluster_router,
    conversation_router,
    deployment_router,
    monitoring_router,
    node_router,
    runtime_router,
    user_router,
)
from apps.cloud.dependencies import require_principal
from apps.cloud.mcp_server.mcp_auth_guard import McpAuthGuard
from apps.cloud.mcp_server.server import mcp
from apps.cloud.mcp_server.tools import (  # noqa: F401  (registers tools)
    deployment_tools,
    fleet_tools,
    monitoring_tools,
)
from apps.cloud.ws import realtime_router
from src.cloud.bootstrap.cloud_container import CloudContainer
from src.cloud.bootstrap.realtime_container import RealtimeContainer
from src.cloud.config.cloud_settings import CloudSettings
from src.shared.exceptions import AppException

API_DESCRIPTION = """
Control plane for the Edge Ops fleet: clusters, nodes, runtimes, deployments and monitoring.

| Interface | Path |
|---|---|
| REST | `/api/v1/...` (this page) |
| WebSocket (edge state / telemetry / events) | `/api/v1/ws?topics=edge/+/+/state&token=<token>` |
| MCP (tools for the assistant) | `/mcp` |
| Health | `/health` |

Edge agents connect to the MQTT broker on port `11883` of the same host.

**Auth:** everything except `/api/v1/auth/{register,login,refresh}`, `/health` and these docs needs
`Authorization: Bearer <token>`, where the token is either
- a user **access token** from `POST /api/v1/auth/login` (expires; renew with `POST /api/v1/auth/refresh`), or
- a service **API key** (`CLOUD_API_KEYS`, for the assistant and scripts; also accepted as `X-API-Key`).

Use **Authorize** above. The first account registered becomes ADMIN.
"""


def create_app(container: CloudContainer, realtime: RealtimeContainer) -> FastAPI:
    dependencies.bind(container, realtime)
    mcp_app = mcp.streamable_http_app(streamable_http_path="/", host="0.0.0.0")

    async def run_mcp(stop: asyncio.Event) -> None:
        # Own task: the session manager's task group must be entered and exited in the same task
        async with mcp.session_manager.run():
            await stop.wait()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await container.start()
        await realtime.start()
        mcp_stop = asyncio.Event()
        tasks = [asyncio.create_task(run_mcp(mcp_stop))]
        if container.settings.embedded_worker:
            await container.subscribe_consumers()
            tasks.append(asyncio.create_task(container.node_liveness_service.run()))
        try:
            yield
        finally:
            mcp_stop.set()
            await tasks[0]
            for task in tasks[1:]:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
            await realtime.stop()
            await container.stop()

    # Docs live under /api so the cluster ingress (which only forwards /api, /mcp, /health) serves them
    app = ServiceApp.create(
        "Edge Ops Cloud",
        lifespan=lifespan,
        health_checks={"database": container.check_database, "redis": container.check_redis,
                       "mqtt": container.check_broker},
        coded_errors=AppException,
        description=API_DESCRIPTION,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.include_router(auth_router.router, prefix="/api/v1")  # public: login/register/refresh
    for module in (
        cluster_router, node_router, agent_router, runtime_router, deployment_router, monitoring_router, user_router,
        conversation_router,
    ):
        app.include_router(module.router, prefix="/api/v1", dependencies=[Depends(require_principal)])
    app.include_router(realtime_router.router, prefix="/api/v1")  # authenticates on connect
    app.mount("/mcp", McpAuthGuard(mcp_app, container.auth_service))
    return app


if __name__ == "__main__":
    os.environ.setdefault("CLOUD_EMBEDDED_WORKER", "true")
    settings = CloudSettings()
    LoggingSetup.configure(settings.service_name, settings.log_level, settings.log_json)
    AccessLogRedactor.install()
    ServiceRunner.run(create_app(CloudContainer(settings), RealtimeContainer(settings)), settings.api_host, settings.api_port)

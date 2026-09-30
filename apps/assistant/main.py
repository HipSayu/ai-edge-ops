"""Assistant (chatbot agent) API. Run: python -m apps.assistant.main (from repo root).

Talks to the Cloud over MCP only; the LangGraph agent + tools live in src/assistant.
"""

from fastapi import Depends, FastAPI, Request
from hopquangdo.http import ApiKeyAuth, ServiceApp, ServiceRunner
from hopquangdo.observability import LoggingSetup

from apps.assistant.api.v1 import chat_router
from src.assistant.bootstrap.assistant_container import AssistantContainer
from src.assistant.config.assistant_settings import AssistantSettings
from src.shared.exceptions import AppException


def create_app(container: AssistantContainer) -> FastAPI:
    checks = {"cloud": container.check_cloud, "redis": container.check_redis, "knowledge": container.check_knowledge}
    app = ServiceApp.create(
        "Edge Ops Assistant API", start=container.start, stop=container.stop, health_checks=checks,
        coded_errors=AppException,
    )
    app.state.container = container
    keys = ApiKeyAuth.static(container.settings.api_keys)

    async def auth(request: Request) -> None:
        """Users come through the API gateway, which verified their token and set X-Auth-Subject (it drops any
        client-sent value; this port is not published). Services use an API key."""
        if not request.headers.get("x-auth-subject"):
            await keys(request)

    app.include_router(chat_router.router, prefix="/api/v1", dependencies=[Depends(auth)])
    return app


if __name__ == "__main__":
    settings = AssistantSettings()
    LoggingSetup.configure(settings.service_name, settings.log_level, settings.log_json)
    ServiceRunner.run(create_app(AssistantContainer(settings)), settings.api_host, settings.api_port)

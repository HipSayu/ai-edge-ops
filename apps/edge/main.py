"""Edge Agent local API (docs/api/Readme.md §4) plus the Runtime -> Agent reporting endpoints.

Run: python -m apps.edge.main (from repo root).
"""

import logging

from fastapi import Depends, FastAPI
from hopquangdo.http import ApiKeyAuth, ServiceApp, ServiceRunner
from hopquangdo.observability import LoggingSetup

from apps.edge.api import reporting_router, runtime_router, status_router
from src.edge.bootstrap.agent_container import AgentContainer
from src.edge.config.agent_settings import AgentSettings
from src.shared.exceptions import AppException


def create_app(container: AgentContainer) -> FastAPI:
    async def stop() -> None:
        await container.agent_service.stop()
        await container.close()

    async def broker_ok() -> bool:
        return container.pubsub.is_connected

    app = ServiceApp.create(
        "Edge Agent API", start=container.agent_service.start, stop=stop, health_checks={"mqtt": broker_ok},
        coded_errors=AppException,
    )
    app.state.container = container
    auth = ApiKeyAuth.static(container.settings.api_keys)
    for module in (status_router, runtime_router, reporting_router):
        app.include_router(module.router, dependencies=[Depends(auth)])
    return app


if __name__ == "__main__":
    settings = AgentSettings()
    LoggingSetup.configure(settings.service_name, settings.log_level, settings.log_json)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # one line per exporter scrape otherwise
    ServiceRunner.run(create_app(AgentContainer(settings)), settings.api_host, settings.api_port)

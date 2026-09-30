"""Service accessors for the Edge Agent routers; `create_app` stores the container on `app.state`."""

from fastapi import Request

from src.edge.application.services.command_service import CommandService
from src.edge.application.services.reporting import StateReportService, TelemetryReportService
from src.edge.application.services.runtime_service import RuntimeService
from src.edge.bootstrap.agent_container import AgentContainer


def get_container(request: Request) -> AgentContainer:
    return request.app.state.container


def get_runtime_service(request: Request) -> RuntimeService:
    return get_container(request).runtime_service


def get_command_service(request: Request) -> CommandService:
    return get_container(request).command_service


def get_state_report_service(request: Request) -> StateReportService:
    return get_container(request).state_report_service


def get_telemetry_report_service(request: Request) -> TelemetryReportService:
    return get_container(request).telemetry_report_service

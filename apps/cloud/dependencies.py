"""Shared service accessors for every Cloud interface (REST routers via Depends, MCP tools, WebSocket).

The Cloud is one process with one container: `create_app` binds it once, everything else reads it here.
"""

from fastapi import Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from src.cloud.application.services.auth_service import AuthService
from src.cloud.application.services.conversation_service import ConversationService
from src.cloud.application.services.deployment_service import DeploymentService
from src.cloud.application.services.entity_resolver import EntityResolver
from src.cloud.application.services.fleet_service import FleetService
from src.cloud.application.services.monitoring_service import MonitoringService
from src.cloud.application.services.realtime_service import RealtimeService
from src.cloud.application.services.user_service import UserService
from src.cloud.bootstrap.cloud_container import CloudContainer
from src.cloud.bootstrap.realtime_container import RealtimeContainer
from src.cloud.domain.value_objects.principal import Principal

_container: CloudContainer | None = None
_realtime: RealtimeContainer | None = None


def bind(container: CloudContainer, realtime: RealtimeContainer) -> None:
    global _container, _realtime
    _container, _realtime = container, realtime


def get_container() -> CloudContainer:
    if _container is None:
        raise RuntimeError("Cloud container not bound; build the app with create_app()")
    return _container


def get_fleet() -> FleetService:
    return get_container().fleet_service


def get_deployment_service() -> DeploymentService:
    return get_container().deployment_service


def get_monitoring() -> MonitoringService:
    return get_container().monitoring_service


def get_resolver() -> EntityResolver:
    return get_container().entity_resolver


def get_conversation_service() -> ConversationService:
    return get_container().conversation_service


def get_auth_service() -> AuthService:
    return get_container().auth_service


# Declared as security schemes so Swagger shows "Authorize"; both are optional here and checked below.
_bearer = HTTPBearer(auto_error=False, description="User access token (POST /auth/login) or service API key")
_api_key = APIKeyHeader(name="X-API-Key", auto_error=False, description="Service API key (CLOUD_API_KEYS)")


async def require_principal(
    bearer: HTTPAuthorizationCredentials | None = Security(_bearer),
    api_key: str | None = Security(_api_key),
) -> Principal:
    """Every protected route depends on this: a user JWT or a service API key, else 401."""
    return await get_auth_service().authenticate(bearer.credentials if bearer else api_key)


def get_user_service() -> UserService:
    return get_container().user_service


def get_realtime_service() -> RealtimeService:
    if _realtime is None:
        raise RuntimeError("Realtime container not bound; build the app with create_app()")
    return _realtime.realtime_service

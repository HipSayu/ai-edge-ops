"""Runs one action on behalf of the caller of an adapter (REST, MCP): the bearer header becomes a viewer, the role is
checked, then the action runs against the container. Adapters differ only in how they turn errors into replies."""

from collections.abc import Callable
from typing import Any

from cloud.bootstrap.container import Container
from shared.errors import Unauthenticated
from shared.roles import Role
from shared.viewer import Viewer


def act_as_caller(
    container: Container, authorization: str, action: Callable[[Container, Viewer], Any], minimum: Role | None = None,
) -> Any:
    if not authorization.lower().startswith("bearer "):
        raise Unauthenticated("Cần đăng nhập")
    viewer = container.auth.authenticate(authorization[7:].strip())
    if minimum is not None:
        viewer.require_role(minimum)
    return action(container, viewer)

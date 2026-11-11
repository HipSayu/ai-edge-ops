"""Acts as the caller of a tool: the bearer token on the MCP request becomes a viewer, the role is checked, then the
action runs on the cloud use cases. Errors reach the client as `<status>: <message>`, the codes the REST API uses."""

import json
from collections.abc import Callable
from typing import Any

import anyio

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError
from cloud.bootstrap.caller import act_as_caller
from cloud.bootstrap.container import Container
from shared.errors import DomainError
from shared.http import status_for
from shared.roles import Role
from shared.viewer import Viewer

_container: Callable[[], Container] | None = None


def bind_container(getter: Callable[[], Container]) -> None:
    """Called once by main. The container only exists after the app starts, so it is fetched per call."""
    global _container
    _container = getter


def _authorization(ctx: Context) -> str:
    request = ctx.request_context.request
    return request.headers.get("authorization", "") if request is not None else ""


async def run(ctx: Context, action: Callable[[Container, Viewer], Any], minimum: Role | None = None) -> str:
    header = _authorization(ctx)
    try:
        value = await anyio.to_thread.run_sync(lambda: act_as_caller(_container(), header, action, minimum))
    except DomainError as error:
        raise ToolError(f"{status_for(error)}: {error}") from error  # the client maps the code back to an error
    return json.dumps(value, ensure_ascii=False)  # one JSON document per result, whatever its shape

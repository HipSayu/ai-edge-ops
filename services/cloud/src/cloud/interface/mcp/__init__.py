"""The PPE MCP server: publishes the tools the cloud service declares (cloud.interface.mcp.tools) over MCP.

It is the one place that knows what tools exist and who may use them. It lists every tool to everyone, so clients can
list once and cache; the role is checked when a tool is called. Every tool says whether it changes data (the client
asks its user before running those)."""

import inspect

from cloud.interface.mcp.runner import run
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from cloud.interface.mcp.tools import TOOLS, Tool


def _adapt(tool: Tool):
    """An MCP handler with the tool's own inputs as its signature (that is what FastMCP turns into the input schema),
    plus the request context, which tells who is calling."""
    inputs = list(inspect.signature(tool.run).parameters.values())[2:]  # after (container, viewer)

    async def handler(ctx: Context, **arguments):
        return await run(ctx, lambda c, v: tool.run(c, v, **arguments), tool.minimum)

    handler.__signature__ = inspect.Signature(
        [inspect.Parameter("ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Context), *inputs])
    handler.__annotations__ = {"ctx": Context}
    return handler


def build_mcp() -> FastMCP:
    # Reached by container name (http://cloud:8100/mcp), so the localhost-only Host check is off; every call needs a token.
    mcp = FastMCP("ppe", stateless_http=True, json_response=True,
                  transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
    for tool in TOOLS:
        mcp.add_tool(_adapt(tool), name=tool.name, description=tool.description,
                     annotations=ToolAnnotations(readOnlyHint=not tool.changes))
    return mcp

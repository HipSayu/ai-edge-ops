"""The AI Edge Ops MCP server — every domain read as an MCP tool.

Mounted at ``/mcp`` by :mod:`app.mcp_main` (its own process; see compose).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.mcp.tools import ALL_TOOLS

INSTRUCTIONS = (
    "Tools for the AI Edge Ops control plane: edge devices and their health, "
    "model registry, deployments, PPE violations, alerts, analytics, cameras, "
    "and system settings. All read-only. Prefer `analytics_overview` for a "
    "top-line summary, then drill in."
)


def build_mcp() -> FastMCP:
    mcp = FastMCP(
        name="ai-edge-ops",
        instructions=INSTRUCTIONS,
        streamable_http_path="/",
        stateless_http=True,
        transport_security=TransportSecuritySettings(
            allowed_hosts=["*"], allowed_origins=["*"]
        ),
    )
    for fn in ALL_TOOLS:
        mcp.add_tool(fn, name=fn.__name__, description=(fn.__doc__ or "").strip())
    return mcp


def build_asgi_app():
    """Streamable-HTTP ASGI app to mount under ``/mcp``."""
    return build_mcp().streamable_http_app()


__all__ = ["build_asgi_app", "build_mcp"]

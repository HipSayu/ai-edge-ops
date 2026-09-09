"""MCP server surface over the domain — see :mod:`app.mcp.server`."""

from __future__ import annotations

from app.mcp.server import build_asgi_app, build_mcp
from app.mcp.tools import ALL_TOOLS

__all__ = ["ALL_TOOLS", "build_asgi_app", "build_mcp"]

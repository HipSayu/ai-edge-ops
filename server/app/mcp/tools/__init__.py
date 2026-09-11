"""Read-only tools over the domain services. One definition, two adapters:
MCP (:mod:`app.mcp.server`) and LangChain (:mod:`app.modules.assistant.toolset`).
"""

from __future__ import annotations

from app.mcp.tools import cameras, deployments, fleet, models, observability, system

# every tool is a plain async function with typed args and a docstring
ALL_TOOLS = [
    *fleet.TOOLS,
    *deployments.TOOLS,
    *models.TOOLS,
    *observability.TOOLS,
    *cameras.TOOLS,
    *system.TOOLS,
]

__all__ = ["ALL_TOOLS"]

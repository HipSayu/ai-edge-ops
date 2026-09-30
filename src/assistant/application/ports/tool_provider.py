from typing import Protocol

from langchain_core.tools import BaseTool


class ToolProvider(Protocol):
    """A source of agent tools defined outside the assistant (e.g. the Cloud MCP server)."""

    async def tools(self) -> list[BaseTool]: ...

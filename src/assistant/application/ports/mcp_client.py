from typing import Any, Protocol

from mcp_types import CallToolResult, Tool


class McpClient(Protocol):
    """An MCP server the assistant calls tools on."""

    async def list_tools(self) -> list[Tool]: ...

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult: ...

    async def ping(self) -> bool: ...

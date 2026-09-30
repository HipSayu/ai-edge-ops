from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp_types import CallToolResult, TextContent, Tool


class CloudMcpClient:
    """Client for the Cloud MCP endpoint (`/mcp/`). The assistant never touches cloud storage directly.

    One short-lived MCP session per call: no long-lived task group to tie to the app lifespan,
    and a Cloud restart never leaves the assistant holding a dead session.
    """

    def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 15.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"X-API-Key": api_key} if api_key else {}
        self._timeout = timeout

    async def list_tools(self) -> list[Tool]:
        async with self._session() as client:
            return (await client.list_tools()).tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        async with self._session() as client:
            return await client.call_tool(name, arguments, read_timeout_seconds=self._timeout)

    async def ping(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as http:
                return (await http.get(f"{self._base_url}/health")).is_success
        except httpx.HTTPError:
            return False

    @asynccontextmanager
    async def _session(self) -> AsyncGenerator[Client]:
        async with httpx2.AsyncClient(headers=self._headers, timeout=self._timeout) as http:
            async with Client(streamable_http_client(f"{self._base_url}/mcp/", http_client=http)) as client:
                yield client

    @staticmethod
    def result_data(result: CallToolResult) -> Any:
        """Structured result when the tool has one, else the joined text; errors become data for the model."""
        text = "\n".join(c.text for c in result.content if isinstance(c, TextContent))
        if result.is_error:
            return {"error": text}
        return result.structured_content if result.structured_content is not None else text

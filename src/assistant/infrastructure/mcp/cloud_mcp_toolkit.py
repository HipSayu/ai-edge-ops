from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from mcp_types import Tool

from src.assistant.application.ports.mcp_client import McpClient
from src.assistant.infrastructure.mcp.cloud_mcp_client import CloudMcpClient


class CloudMcpToolkit:
    """LangChain tools generated from the Cloud MCP server, so tools are defined once (in the Cloud).

    Cloud errors are returned to the model as data instead of raised, so the agent can explain or retry.
    """

    def __init__(self, client: McpClient) -> None:
        self._client = client

    async def tools(self) -> list[BaseTool]:
        specs = await self._client.list_tools()
        return [self._to_langchain(s) for s in specs]

    def _to_langchain(self, spec: Tool) -> BaseTool:
        client = self._client

        async def call(**arguments: Any) -> Any:
            try:
                result = await client.call_tool(spec.name, arguments)
            except Exception as exc:  # transport failure: surface to the model, don't crash the graph
                return {"error": "cloud_unreachable", "detail": str(exc)}
            return CloudMcpClient.result_data(result)

        return StructuredTool.from_function(
            coroutine=call, name=spec.name, description=spec.description or spec.name, args_schema=spec.input_schema
        )

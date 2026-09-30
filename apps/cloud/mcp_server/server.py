"""The MCPServer instance tools register on (like a module-level APIRouter). Services come from apps.cloud.dependencies."""

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("edge-ops-cloud")

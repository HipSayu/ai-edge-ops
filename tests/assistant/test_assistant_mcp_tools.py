"""Assistant tools are generated from the Cloud MCP server (in-process here instead of over HTTP)."""

from typing import Any

import pytest
from hopquangdo.messaging.adapters.memory import InMemoryPubSub
from mcp import Client

from apps.cloud.main import create_app
from apps.cloud.mcp_server.server import mcp
from src.assistant.infrastructure.mcp.cloud_mcp_toolkit import CloudMcpToolkit
from src.cloud.bootstrap.cloud_container import CloudContainer
from src.cloud.bootstrap.realtime_container import RealtimeContainer
from src.cloud.config.cloud_settings import CloudSettings
from tests.fakes.cloud.fake_cloud_repositories import FakeCloudRepositories


class InProcessMcpClient:
    """Same surface as CloudMcpClient, talking to the MCPServer object directly."""

    async def list_tools(self):
        async with Client(mcp) as client:
            return (await client.list_tools()).tools

    async def call_tool(self, name: str, arguments: dict[str, Any]):
        async with Client(mcp) as client:
            return await client.call_tool(name, arguments)

    async def ping(self) -> bool:
        return True


@pytest.fixture
async def cloud():
    settings = CloudSettings()
    app = create_app(CloudContainer(settings, pubsub=InMemoryPubSub(), repositories=FakeCloudRepositories.create()), RealtimeContainer(settings, pubsub=InMemoryPubSub()))
    async with app.router.lifespan_context(app):
        yield


async def test_read_only_by_default(cloud):
    names = {t.name for t in await CloudMcpToolkit(InProcessMcpClient()).tools()}
    assert {"list_nodes", "get_latest_telemetry"} <= names
    assert not names & {"create_deployment", "remove_deployment", "control_runtime", "create_cluster"}


async def test_write_tools_when_allowed_and_calls_reach_cloud(cloud):
    tools = {t.name: t for t in await CloudMcpToolkit(InProcessMcpClient()).tools()}
    cluster = await tools["create_cluster"].ainvoke({"name": "site-a"})
    assert cluster["name"] == "site-a"
    listed = await tools["list_clusters"].ainvoke({})
    assert "site-a" in str(listed)


async def test_errors_are_returned_as_data(cloud):
    tools = {t.name: t for t in await CloudMcpToolkit(InProcessMcpClient()).tools()}
    result = await tools["get_node"].ainvoke({"node": "missing"})
    assert "error" in result

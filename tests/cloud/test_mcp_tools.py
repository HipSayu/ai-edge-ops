import pytest
from hopquangdo.messaging.adapters.memory import InMemoryPubSub

from apps.cloud.main import create_app
from apps.cloud.mcp_server.server import mcp
from apps.cloud.mcp_server.tools import fleet_tools
from src.cloud.bootstrap.cloud_container import CloudContainer
from src.cloud.bootstrap.realtime_container import RealtimeContainer
from src.cloud.config.cloud_settings import CloudSettings
from src.shared.exceptions import AppException, ErrorCode
from tests.fakes.cloud.fake_cloud_repositories import FakeCloudRepositories


def _app():
    settings = CloudSettings()
    container = CloudContainer(settings, pubsub=InMemoryPubSub(), repositories=FakeCloudRepositories.create())
    return create_app(container, RealtimeContainer(settings, pubsub=InMemoryPubSub()))


async def test_tools_registered():
    names = {t.name for t in await mcp.list_tools()}
    assert {"list_nodes", "create_deployment", "control_runtime", "get_latest_telemetry"} <= names


async def test_tools_share_the_app_container():
    app = _app()
    async with app.router.lifespan_context(app):
        cluster = await fleet_tools.create_cluster("site-a")
        node = await fleet_tools.register_node(cluster["id"], "jetson-1")
        assert [n["id"] for n in await fleet_tools.list_nodes(cluster["id"])] == [node["id"]]


async def test_tools_take_names_and_codes_instead_of_ids():
    app = _app()
    async with app.router.lifespan_context(app):
        await fleet_tools.create_cluster("Công trường A - Thi công móng", metadata={"site_code": "CT-A"})
        await fleet_tools.create_cluster("Công trường B", metadata={"site_code": "CT-B"})
        await fleet_tools.register_node("CT-A", "Hố móng", {"code": "CT-A-01"})
        await fleet_tools.register_node("CT-B", "Hố móng")

        # Names without diacritics, codes, and "cluster/node" all reach the same node
        by_code = await fleet_tools.get_node("CT-A-01")
        assert by_code["name"] == "Hố móng" and by_code["cluster"] == "Công trường A - Thi công móng"
        assert (await fleet_tools.get_node("ct-a/ho mong"))["id"] == by_code["id"]
        assert (await fleet_tools.get_node("Hố móng", cluster="Công trường A"))["id"] == by_code["id"]
        assert [n["name"] for n in await fleet_tools.list_nodes("ct-b")] == ["Hố móng"]

        # Two nodes named "Hố móng": ask instead of guessing
        with pytest.raises(AppException) as ambiguous:
            await fleet_tools.get_node("Hố móng")
        assert ambiguous.value.code == ErrorCode.INVALID_REQUEST

        # Writes need an exact reference: a partial cluster name is refused
        with pytest.raises(AppException) as partial:
            await fleet_tools.register_node("Công trường A", "Tầng hầm")
        assert partial.value.code == ErrorCode.NOT_FOUND
        created = await fleet_tools.register_node("CT-A", "Tầng hầm")
        assert created["cluster"] == "Công trường A - Thi công móng"

        overview = await fleet_tools.get_node_overview("CT-A-01")
        assert overview["node"]["code"] == "CT-A-01" and overview["runtimes"] == []

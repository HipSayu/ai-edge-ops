from datetime import timedelta

import httpx
import pytest
from hopquangdo.messaging import Message
from hopquangdo.messaging.adapters.memory import InMemoryPubSub

from apps.cloud.main import create_app
from src.cloud.bootstrap.cloud_container import CloudContainer
from src.cloud.bootstrap.realtime_container import RealtimeContainer
from src.cloud.config.cloud_settings import CloudSettings
from src.cloud.domain.value_objects.node_heartbeat import NodeHeartbeat
from src.shared.contracts import EdgeTopics, NodeStatus
from src.shared.domain.clock import Clock
from tests.fakes.cloud.fake_cloud_repositories import FakeCloudRepositories

AUTH = {"Authorization": "Bearer svc"}


@pytest.fixture
async def cloud():
    settings = CloudSettings(api_keys=["svc"])
    container = CloudContainer(settings, pubsub=InMemoryPubSub(), repositories=FakeCloudRepositories.create())
    app = create_app(container, RealtimeContainer(settings, pubsub=InMemoryPubSub()))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://cloud", headers=AUTH) as c:
            yield c, container


async def test_cluster_and_node_update_and_delete(cloud):
    c, container = cloud
    cluster = (await c.post("/api/v1/clusters", json={"name": "ppe-site"})).json()
    node = (await c.post("/api/v1/nodes", json={"cluster_id": cluster["id"], "name": "gate"})).json()

    r = await c.patch(f"/api/v1/clusters/{cluster['id']}", json={"location": "Hà Nội", "name": "ppe-hn"})
    assert r.status_code == 200 and r.json()["location"] == "Hà Nội" and r.json()["name"] == "ppe-hn"
    r = await c.patch(f"/api/v1/nodes/{node['id']}", json={"metadata": {"zone": "Gate"}})
    assert r.json()["metadata"] == {"zone": "Gate"} and r.json()["name"] == "gate"

    # an online node blocks deletion (its runtimes would be orphaned on the edge)
    await container.nodes.apply_heartbeat(NodeHeartbeat(node_id=node["id"], status=NodeStatus.ONLINE, at=Clock.now()))
    assert (await c.delete(f"/api/v1/clusters/{cluster['id']}")).status_code == 409
    assert (await c.delete(f"/api/v1/nodes/{node['id']}")).status_code == 409

    await container.nodes.mark_offline_before(Clock.now() + timedelta(seconds=1))
    assert (await c.delete(f"/api/v1/nodes/{node['id']}")).status_code == 204
    assert (await c.delete(f"/api/v1/clusters/{cluster['id']}")).status_code == 204
    assert (await c.get(f"/api/v1/clusters/{cluster['id']}")).status_code == 404


async def test_runtime_logs_are_stored_and_served(cloud):
    c, container = cloud
    cluster = (await c.post("/api/v1/clusters", json={"name": "s"})).json()
    node = (await c.post("/api/v1/nodes", json={"cluster_id": cluster["id"], "name": "n"})).json()
    dep = (await c.post("/api/v1/deployments", json={"node_id": node["id"], "name": "ppe", "image_uri": "img"})).json()
    runtime_id = dep["runtime_id"]

    batch = {"node_id": node["id"], "runtime_id": runtime_id, "runtime_name": "ppe", "lines": [
        {"timestamp": "2026-09-29T03:00:00Z", "level": "INFO", "message": "model loaded"},
        {"timestamp": "2026-09-29T03:00:01Z", "level": "ERROR", "message": "camera 2 timeout"},
    ]}
    topic = EdgeTopics(cluster["id"], node["id"]).logs(runtime_id)
    await container.runtime_log_handler.handle(Message(topic=topic, payload=batch))

    logs = (await c.get(f"/api/v1/runtimes/{runtime_id}/logs")).json()
    assert [line["message"] for line in logs] == ["model loaded", "camera 2 timeout"]
    assert logs[1]["level"] == "ERROR" and logs[0]["runtime_name"] == "ppe"
    assert (await c.get("/api/v1/runtimes/nope/logs")).status_code == 404


async def test_fleet_metrics_shape(cloud):
    c, _ = cloud
    points = (await c.get("/api/v1/monitoring/fleet/metrics", params={"points": 6})).json()
    assert len(points) == 6
    assert set(points[0]) == {"time", "fps", "latency", "throughput", "gpu", "alert", "healthyClusters",
                              "onlineNodes", "onlineCameras"}


async def test_user_admin(cloud):
    c, _ = cloud
    created = await c.post("/api/v1/users", json={"username": "ops", "email": "ops@x.io", "password": "long-enough"})
    assert created.status_code == 201 and created.json()["role"] == "ADMIN"
    user_id = created.json()["id"]
    assert len((await c.get("/api/v1/users")).json()) == 1
    r = await c.patch(f"/api/v1/users/{user_id}", json={"displayName": "Operator"})
    assert r.json()["displayName"] == "Operator"
    # the only active account cannot be disabled
    assert (await c.patch(f"/api/v1/users/{user_id}", json={"status": "SUSPENDED"})).status_code == 409

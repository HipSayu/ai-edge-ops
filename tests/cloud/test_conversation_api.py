import httpx
import pytest
from hopquangdo.messaging.adapters.memory import InMemoryPubSub

from apps.cloud.main import create_app
from src.cloud.bootstrap.cloud_container import CloudContainer
from src.cloud.bootstrap.realtime_container import RealtimeContainer
from src.cloud.config.cloud_settings import CloudSettings
from tests.fakes.cloud.fake_cloud_repositories import FakeCloudRepositories

ALICE = {"username": "alice", "email": "alice@example.com", "password": "correct-horse-1"}
BOB = {"username": "bob", "email": "bob@example.com", "password": "correct-horse-2"}


@pytest.fixture
async def client():
    settings = CloudSettings(api_keys=["svc-key"], access_token_ttl_min=5)
    container = CloudContainer(settings, pubsub=InMemoryPubSub(), repositories=FakeCloudRepositories.create())
    app = create_app(container, RealtimeContainer(settings, pubsub=InMemoryPubSub()))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://cloud") as c:
            yield c


@pytest.fixture
async def users(client):
    """Alice (first account) and Bob (created by Alice); their auth headers."""
    alice = (await client.post("/api/v1/auth/register", json=ALICE)).json()["accessToken"]
    headers_a = {"Authorization": f"Bearer {alice}"}
    assert (await client.post("/api/v1/users", json=BOB, headers=headers_a)).status_code == 201
    login = await client.post("/api/v1/auth/login", json={"login": "bob", "password": BOB["password"]})
    return headers_a, {"Authorization": f"Bearer {login.json()['accessToken']}"}


async def test_conversation_lifecycle(client, users):
    alice, _ = users
    first = (await client.post("/api/v1/conversations", json={}, headers=alice)).json()
    second = (await client.post("/api/v1/conversations", json={"title": "Báo cáo"}, headers=alice)).json()
    assert first["title"] is None and {"id", "createdAt", "updatedAt"} <= first.keys()

    # the first question names an untitled conversation, and moves it to the top
    message = {"role": "USER", "content": "Node nào đang offline?"}
    assert (await client.post(f"/api/v1/conversations/{first['id']}/messages", json=message, headers=alice)).status_code == 201
    reply = {"role": "ASSISTANT", "content": "Không có node nào.", "metadata": {"trace": [{"kind": "tool", "tool": "list_nodes"}]}}
    await client.post(f"/api/v1/conversations/{first['id']}/messages", json=reply, headers=alice)

    listed = (await client.get("/api/v1/conversations", headers=alice)).json()
    assert [(c["id"], c["title"]) for c in listed] == [(first["id"], "Node nào đang offline?"), (second["id"], "Báo cáo")]

    messages = (await client.get(f"/api/v1/conversations/{first['id']}/messages", headers=alice)).json()
    assert [m["role"] for m in messages] == ["USER", "ASSISTANT"]
    assert messages[1]["metadata"]["trace"][0]["tool"] == "list_nodes"

    renamed = await client.patch(f"/api/v1/conversations/{first['id']}", json={"title": "Offline"}, headers=alice)
    assert renamed.json()["title"] == "Offline"
    assert (await client.delete(f"/api/v1/conversations/{first['id']}", headers=alice)).status_code == 204
    assert [c["id"] for c in (await client.get("/api/v1/conversations", headers=alice)).json()] == [second["id"]]


async def test_users_only_see_their_own_conversations(client, users):
    alice, bob = users
    mine = (await client.post("/api/v1/conversations", json={"title": "Alice"}, headers=alice)).json()

    assert (await client.get("/api/v1/conversations", headers=bob)).json() == []
    assert (await client.get(f"/api/v1/conversations/{mine['id']}/messages", headers=bob)).status_code == 404
    assert (await client.delete(f"/api/v1/conversations/{mine['id']}", headers=bob)).status_code == 404
    assert (await client.get("/api/v1/conversations/not-a-uuid/messages", headers=alice)).status_code == 404


async def test_service_keys_have_no_conversations(client):
    assert (await client.get("/api/v1/conversations", headers={"X-API-Key": "svc-key"})).status_code == 403
    assert (await client.get("/api/v1/conversations")).status_code == 401

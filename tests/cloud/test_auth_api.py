import httpx
import pytest
from hopquangdo.messaging.adapters.memory import InMemoryPubSub

from apps.cloud.main import create_app
from src.cloud.bootstrap.cloud_container import CloudContainer
from src.cloud.bootstrap.realtime_container import RealtimeContainer
from src.cloud.config.cloud_settings import CloudSettings
from tests.fakes.cloud.fake_cloud_repositories import FakeCloudRepositories

ADMIN = {"username": "admin", "email": "Admin@Example.com", "password": "correct-horse-1", "displayName": "Ops"}


@pytest.fixture
async def client():
    settings = CloudSettings(api_keys=["svc-key"], access_token_ttl_min=5)
    container = CloudContainer(settings, pubsub=InMemoryPubSub(), repositories=FakeCloudRepositories.create())
    app = create_app(container, RealtimeContainer(settings, pubsub=InMemoryPubSub()))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://cloud") as c:
            yield c


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_every_protected_route_needs_credentials(client):
    assert (await client.get("/api/v1/clusters")).status_code == 401
    assert (await client.get("/api/v1/clusters", headers=bearer("garbage"))).status_code == 401
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    assert (await client.post("/mcp/", json={})).status_code == 401
    # public
    assert (await client.get("/health")).status_code == 200
    assert (await client.get("/api/docs")).status_code == 200


async def test_register_login_refresh_logout(client):
    r = await client.post("/api/v1/auth/register", json=ADMIN)
    assert r.status_code == 201
    session = r.json()
    assert session["user"]["role"] == "ADMIN"  # first account
    assert session["user"]["email"] == "admin@example.com"
    assert session["tokenType"] == "Bearer" and session["expiresIn"] == 300
    assert "passwordHash" not in session["user"]

    assert (await client.get("/api/v1/clusters", headers=bearer(session["accessToken"]))).status_code == 200

    # registration is closed once an admin exists
    second = {"username": "bob", "email": "bob@example.com", "password": "correct-horse-2"}
    assert (await client.post("/api/v1/auth/register", json=second)).status_code == 403

    assert (await client.post("/api/v1/auth/login", json={"login": "admin", "password": "nope"})).status_code == 401
    assert (await client.post("/api/v1/auth/login", json={"login": "ghost", "password": "nope"})).status_code == 401
    login = (await client.post("/api/v1/auth/login", json={"login": "ADMIN@example.com", "password": ADMIN["password"]}))
    assert login.status_code == 200
    tokens = login.json()

    me = await client.get("/api/v1/auth/me", headers=bearer(tokens["accessToken"]))
    assert me.json()["username"] == "admin" and me.json()["lastLoginAt"] is not None

    refreshed = await client.post("/api/v1/auth/refresh", json={"refreshToken": tokens["refreshToken"]})
    assert refreshed.status_code == 200
    # rotation: the old refresh token is single-use
    assert (await client.post("/api/v1/auth/refresh", json={"refreshToken": tokens["refreshToken"]})).status_code == 401

    new = refreshed.json()
    r = await client.post("/api/v1/auth/logout", json={"refreshToken": new["refreshToken"]}, headers=bearer(new["accessToken"]))
    assert r.status_code == 204
    assert (await client.post("/api/v1/auth/refresh", json={"refreshToken": new["refreshToken"]})).status_code == 401


async def test_service_api_key_still_works(client):
    assert (await client.get("/api/v1/clusters", headers=bearer("svc-key"))).status_code == 200
    assert (await client.get("/api/v1/clusters", headers={"X-API-Key": "svc-key"})).status_code == 200
    # a service key is not a user
    assert (await client.get("/api/v1/auth/me", headers=bearer("svc-key"))).status_code == 404


async def test_register_validation(client):
    bad = {"username": "a", "email": "not-an-email", "password": "short"}
    assert (await client.post("/api/v1/auth/register", json=bad)).status_code == 422
    await client.post("/api/v1/auth/register", json=ADMIN)

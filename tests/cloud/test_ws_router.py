import pytest
from fastapi.testclient import TestClient
from hopquangdo.messaging.adapters.memory import InMemoryPubSub
from starlette.websockets import WebSocketDisconnect

from apps.cloud.main import create_app
from src.cloud.bootstrap.cloud_container import CloudContainer
from src.cloud.bootstrap.realtime_container import RealtimeContainer
from src.cloud.config.cloud_settings import CloudSettings
from tests.fakes.cloud.fake_cloud_repositories import FakeCloudRepositories


def _app(api_keys: list[str] | None = None):
    broker = InMemoryPubSub()
    settings = CloudSettings(api_keys=api_keys or ["s3cret"])
    container = CloudContainer(settings, pubsub=InMemoryPubSub(), repositories=FakeCloudRepositories.create())
    return create_app(container, RealtimeContainer(settings, pubsub=broker)), broker


def test_ws_streams_matching_topics():
    app, broker = _app()
    with TestClient(app) as client:
        with client.websocket_connect("/api/v1/ws?topics=edge/c1/n1/telemetry/+&token=s3cret") as ws:
            ws.portal.call(broker.publish, "edge/c1/n2/telemetry/system", {"node_id": "n2"})  # filtered out
            ws.portal.call(broker.publish, "edge/c1/n1/telemetry/system", {"node_id": "n1", "cpu_usage_pct": 5})
            msg = ws.receive_json()
            assert msg["topic"] == "edge/c1/n1/telemetry/system"
            assert msg["payload"]["cpu_usage_pct"] == 5

            ws.send_json({"action": "subscribe", "topics": ["edge/+/+/event/+"]})
            assert ws.receive_json()["action"] == "ack"
            ws.send_json({"action": "unsubscribe", "topics": ["edge/c1/n1/telemetry/+"]})
            assert ws.receive_json() == {"action": "ack", "topics": ["edge/+/+/event/+"]}

            ws.portal.call(broker.publish, "edge/c1/n1/telemetry/system", {"node_id": "n1"})  # now filtered
            ws.portal.call(broker.publish, "edge/c9/n9/event/error", {"node_id": "n9", "message": "boom"})
            assert ws.receive_json()["topic"] == "edge/c9/n9/event/error"


def test_ws_rejects_bad_or_missing_credentials():
    app, _ = _app(["s3cret"])
    with TestClient(app) as client:
        for query in ("", "?token=wrong"):
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect(f"/api/v1/ws{query}") as ws:
                    ws.receive_json()
        with client.websocket_connect("/api/v1/ws?api_key=s3cret"):  # deprecated alias still works
            pass


def test_ws_accepts_user_access_token():
    app, _ = _app()
    with TestClient(app) as client:
        body = {"username": "ops", "email": "ops@example.com", "password": "correct-horse"}
        token = client.post("/api/v1/auth/register", json=body).json()["accessToken"]
        with client.websocket_connect(f"/api/v1/ws?token={token}"):
            pass

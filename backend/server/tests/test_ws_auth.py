from __future__ import annotations

import datetime as dt

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from app.core.token_codec import token_codec
from app.main import create_app


async def test_local_env_allows_anonymous_socket(_engine):
    app = create_app()
    with TestClient(app) as client, client.websocket_connect("/api/v1/agent/ws/telemetry") as ws:
        ws.send_json({"op": "snapshot"})  # handshake succeeds, no token needed


async def test_non_local_env_rejects_missing_token(_engine, monkeypatch):
    monkeypatch.setattr(settings, "environment", "staging")
    app = create_app()
    with TestClient(app) as client:  # noqa: SIM117
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/v1/agent/ws/telemetry"):
                pass


async def test_non_local_env_accepts_valid_token(_engine, session, monkeypatch):
    from app.modules.user.models import User

    user = User(email="ops@example.com", name="Ops", active=True, password_hash="x")
    session.add(user)
    await session.commit()

    monkeypatch.setattr(settings, "environment", "staging")
    token, _ = token_codec.encode(str(user.id), "access", dt.timedelta(minutes=5))

    app = create_app()
    with TestClient(app) as client, client.websocket_connect(
        f"/api/v1/agent/ws/telemetry?token={token}"
    ) as ws:
        ws.send_json({"op": "snapshot"})

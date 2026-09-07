from __future__ import annotations

import json

from starlette.testclient import TestClient

import edge_protocol as protocol
from app.core.ws import ws_hub
from app.main import create_app
from dqh.svc_core.messaging import Envelope


async def test_edge_log_is_pushed_to_frontend(_engine):
    fastapi_app = create_app()

    with TestClient(fastapi_app) as client, client.websocket_connect("/api/v1/agent/ws/logs") as ws:
        await ws_hub.publish(
            "logs/edge-dev-1",
            Envelope(
                type=protocol.T_LOG,
                source="edge-dev-1",
                payload={
                    "device_id": "edge-dev-1",
                    "level": "ERROR",
                    "logger": "edge_agent.pipeline",
                    "message": "inference failed",
                    "recorded_at": "2026-09-05T10:00:00Z",
                    "exception": "RuntimeError: failed",
                },
            ),
        )
        message = json.loads(ws.receive_text())

    assert message["type"] == protocol.T_LOG
    assert message["source"] == "edge-dev-1"
    assert message["payload"]["message"] == "inference failed"

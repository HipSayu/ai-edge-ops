from __future__ import annotations

import json

from starlette.testclient import TestClient

from app.main import create_app


async def test_alert_raised_is_pushed_over_websocket(_engine):
    fastapi_app = create_app()

    with TestClient(fastapi_app) as client, client.websocket_connect("/api/v1/ws/alerts") as ws:
        device = client.post(
            "/api/v1/agent/devices",
            json={"name": "cam-01", "site": "Plant A", "hardware": "Jetson Orin Nano"},
        ).json()["data"]

        resp = client.post(
            "/api/v1/violations",
            json={
                "device_id": device["id"],
                "zone": "loading-bay",
                "violation_type": "no_helmet",
                "confidence": 0.91,
            },
        )
        assert resp.status_code == 201

        raw = ws.receive_text()

    data = json.loads(raw)
    assert data["type"] == "alert.created"
    assert data["payload"]["type"] == "ppe_violation"
    assert data["payload"]["device_id"] == device["id"]

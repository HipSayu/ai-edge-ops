from __future__ import annotations

import json

from starlette.testclient import TestClient

from app.main import create_app


async def test_heartbeat_is_pushed_as_device_sample_and_agent_aggregate(_engine):
    fastapi_app = create_app()

    with TestClient(fastapi_app) as client, client.websocket_connect("/api/v1/agent/ws/telemetry") as ws:
        device = client.post(
            "/api/v1/agent/devices",
            json={"device_id": "cam-01", "name": "cam-01", "site": "Plant A", "hardware": "Jetson Orin Nano"},
        ).json()["data"]

        resp = client.post(
            f"/api/v1/agent/devices/{device['device_id']}/heartbeat",
            json={"fps": 24.0, "inference_latency_ms": 18.5, "cpu_percent": 40.0, "gpu_percent": 55.0},
        )
        assert resp.status_code == 201

        device_msg = json.loads(ws.receive_text())
        agent_msg = json.loads(ws.receive_text())

    assert device_msg["type"] == "telemetry.device"
    assert device_msg["payload"]["device_id"] == device["device_id"]
    assert device_msg["payload"]["fps"] == 24.0

    assert agent_msg["type"] == "telemetry.agent"
    assert agent_msg["payload"]["devices_reporting"] == 1
    assert agent_msg["payload"]["fps_avg"] == 24.0
    assert agent_msg["payload"]["inference_latency_ms_avg"] == 18.5

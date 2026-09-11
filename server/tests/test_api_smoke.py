from __future__ import annotations


async def test_health(client):
    resp = await client.get("health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_violation_flow_creates_alert_and_shows_in_analytics(client):
    device = (
        await client.post(
            "agent/devices",
            json={"device_id": "cam-01", "name": "cam-01", "site": "Plant A", "hardware": "Jetson Orin Nano"},
        )
    ).json()["data"]

    resp = await client.post(
        "violations",
        json={
            "device_id": device["device_id"],
            "zone": "loading-bay",
            "violation_type": "no_helmet",
            "confidence": 0.91,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["success"] is True

    alerts = (await client.get("alerts")).json()["data"]
    assert alerts["total"] == 1
    assert alerts["items"][0]["type"] == "ppe_violation"

    overview = (await client.get("analytics/overview")).json()["data"]
    assert overview["violations_24h"] == 1
    assert overview["open_alerts"] == 1
    assert overview["devices_total"] == 1


async def test_not_found_is_enveloped(client):
    resp = await client.get("agent/devices/999999")
    assert resp.status_code == 404
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NOT_FOUND"


async def test_camera_system_and_assistant_endpoints_persist_data(client):
    camera = (
        await client.post(
            "agent/cameras",
            json={"name": "demo-camera", "source": "/media/demo.mp4", "zone": "test"},
        )
    ).json()["data"]
    cameras = (await client.get("agent/cameras")).json()["data"]
    assert cameras[0]["id"] == camera["id"]
    assert cameras[0]["source"] == "/media/demo.mp4"

    user = (
        await client.post(
            "users",
            json={"name": "Test Operator", "email": "test@example.com", "role": "operator"},
        )
    ).json()["data"]
    assert (await client.get(f"users/{user['id']}" )).json()["data"]["email"] == "test@example.com"

    settings = (await client.patch("system/settings", json={"confidence_threshold": 0.5})).json()["data"]
    assert settings["confidence_threshold"]["value"]["value"] == 0.5

    # `/help` is a direct slash command — deterministic, no LLM. The endpoint
    # returns the assistant reply; both turns are persisted.
    reply = (await client.post("assistant/messages", json={"text": "/help"})).json()["data"]
    assert reply["role"] == "assistant"
    history = (await client.get("assistant/messages")).json()["data"]
    assert [m["text"] for m in history[:2]] == ["/help", reply["text"]]

from __future__ import annotations


async def test_health(client):
    resp = await client.get("health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_violation_flow_creates_alert_and_shows_in_analytics(client):
    device = (
        await client.post(
            "fleet/devices",
            json={"name": "cam-01", "site": "Plant A", "hardware": "Jetson Orin Nano"},
        )
    ).json()["data"]

    resp = await client.post(
        "violations",
        json={
            "device_id": device["id"],
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
    resp = await client.get("fleet/devices/999999")
    assert resp.status_code == 404
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NOT_FOUND"

from __future__ import annotations

import asyncio

import edge_protocol as protocol
import pytest
from dqh.svc_core.messaging import Envelope, InMemoryMessageBus

from app.core.fleet import fleet
from app.core.ws import ws_hub
from app.edge.gateway import AgentGateway
from app.modules.agent import telemetry_relay
from app.modules.agent.rules import DeviceStatus
from app.modules.agent.schemas import DeviceCreate
from app.modules.agent.service import AgentService
from app.modules.observability.repository import AlertRepository, ViolationRepository


@pytest.fixture
async def gateway(_engine):
    bus = InMemoryMessageBus()
    await bus.connect()
    gw = AgentGateway(bus)
    await gw.start()
    yield gw
    await gw.stop()


def _noop():
    return asyncio.sleep(0)


async def _new_device(session) -> int:
    device = await AgentService(session).register_device(
        DeviceCreate(device_id="cam-01", name="cam-01", site="Plant A", hardware="Jetson Orin Nano")
    )
    return device.device_id


async def test_heartbeat_over_bus_updates_device_and_presence(gateway, session):
    device_id = await _new_device(session)

    await gateway.bus.publish(
        protocol.TOPIC_STATE.render(device_id=str(device_id)),
        Envelope(
            type=protocol.T_HEARTBEAT,
            source=str(device_id),
            payload=protocol.HeartbeatPayload(
                inference_latency_ms=15.0,
                active_image="ghcr.io/acme/model@sha256:7",
                capabilities=protocol.DeviceCapabilities(
                    agent_version="1.2.3", ip_address="10.0.0.5", uptime_s=42.0
                ),
            ).model_dump(mode="json"),
        ),
    )

    rs = fleet.get(device_id)
    assert rs is not None
    assert rs.status() is DeviceStatus.ONLINE
    assert rs.last_seen_at is not None
    assert rs.agent_version == "1.2.3"
    assert rs.ip_address == "10.0.0.5"
    assert rs.uptime_s == 42.0
    assert rs.active_image == "ghcr.io/acme/model@sha256:7"


async def test_telemetry_over_bus_fans_out_and_downsamples(gateway, session):
    telemetry_relay.reset_cache()
    if not ws_hub.connected:
        await ws_hub.connect()
    device_id = await _new_device(session)

    received: list = []

    async def _capture(env) -> None:
        received.append(env)

    sub = await ws_hub.subscribe(f"telemetry/{device_id}", _capture)

    await gateway.bus.publish(
        protocol.TOPIC_TELEMETRY.render(device_id=str(device_id)),
        Envelope(
            type=protocol.T_TELEMETRY,
            source=str(device_id),
            payload=protocol.TelemetryPayload(
                samples=[
                    protocol.HeartbeatPayload(cpu_percent=10.0, mem_used_mb=1000.0),
                    protocol.HeartbeatPayload(cpu_percent=20.0, mem_used_mb=1100.0),
                ]
            ).model_dump(mode="json"),
        ),
    )
    await sub.unsubscribe()

    # every sample fanned out live (a 3rd echo comes from the once-a-minute
    # downsample-persist re-emitting the latest sample as a HeartbeatRecorded)
    assert [e.payload["cpu_percent"] for e in received][:2] == [10.0, 20.0]
    assert all(e.payload["device_id"] == device_id for e in received)

    assert fleet.get(device_id).status() is DeviceStatus.ONLINE


async def test_violation_over_bus_records_and_alerts(gateway, session):
    device_id = await _new_device(session)

    await gateway.bus.publish(
        protocol.TOPIC_EVENTS.render(device_id=str(device_id)),
        Envelope(
            type=protocol.T_VIOLATION,
            source=str(device_id),
            payload=protocol.ViolationPayload(
                zone="loading-bay", violation_type="no_helmet", confidence=0.92
            ).model_dump(mode="json"),
        ),
    )

    violations = await ViolationRepository(session).list()
    alerts = await AlertRepository(session).list()
    assert len(violations) == 1
    assert violations[0].device_id == device_id
    assert any(a.type.value == "ppe_violation" for a in alerts)


async def test_deploy_requested_sends_the_image(gateway, session):
    from app.modules.deployment.event import DeployRequested

    device_id = await _new_device(session)

    sent: list = []
    await gateway.bus.subscribe(
        protocol.TOPIC_CMD.render(device_id=str(device_id)),
        lambda e: sent.append(e) or _noop(),
    )
    await gateway._on_deploy_requested(
        DeployRequested(
            device_id=device_id,
            image="ghcr.io/acme/model@sha256:gpu",
            config={"conf_threshold": 0.4},
        )
    )

    assert sent, "no deploy command sent"
    payload = protocol.DeployModelPayload.model_validate(sent[-1].payload)
    assert payload.image == "ghcr.io/acme/model@sha256:gpu"
    assert payload.config == {"conf_threshold": 0.4}


async def test_config_change_pushes_update_config(gateway, session):
    from app.modules.agent.schemas import DeviceCreate, DeviceUpdate
    from app.modules.deployment.subscribers import DeploymentSubscribers

    DeploymentSubscribers().register()
    await AgentService(session).register_device(
        DeviceCreate(device_id="cam-9", name="cam-9", site="A")
    )

    sent: list = []
    await gateway.bus.subscribe(
        protocol.TOPIC_CMD.render(device_id="cam-9"),
        lambda e: sent.append(e) or _noop(),
    )
    await AgentService(session).update_device(
        "cam-9", DeviceUpdate(inference={"conf_threshold": 0.6})
    )
    await asyncio.sleep(0.02)

    assert sent, "no T_UPDATE_CONFIG sent"
    p = protocol.UpdateConfigPayload.model_validate(sent[-1].payload)
    assert p.config == {"conf_threshold": 0.6}

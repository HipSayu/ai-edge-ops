from __future__ import annotations

import pytest
from dqh.svc_core.messaging import Envelope, InMemoryMessageBus

import edge_protocol as protocol
from app.edge.gateway import FleetGateway
from app.modules.fleet.domain import DeviceStatus
from app.modules.fleet.schemas import DeviceCreate
from app.modules.fleet.service import FleetService
from app.modules.observability.repository import AlertRepository, ViolationRepository


@pytest.fixture
async def gateway(_engine):
    bus = InMemoryMessageBus()
    await bus.connect()
    gw = FleetGateway(bus)
    await gw.start()
    yield gw
    await gw.stop()


async def _new_device(session) -> int:
    device = await FleetService(session).register_device(
        DeviceCreate(name="cam-01", site="Plant A", hardware="Jetson Orin Nano")
    )
    return device.id


async def test_heartbeat_over_bus_updates_device_and_presence(gateway, session):
    device_id = await _new_device(session)

    await gateway.bus.publish(
        protocol.TOPIC_STATE.render(device_id=str(device_id)),
        Envelope(
            type=protocol.T_HEARTBEAT,
            source=str(device_id),
            payload=protocol.HeartbeatPayload(inference_latency_ms=15.0).model_dump(mode="json"),
        ),
    )

    session.expire_all()  # gateway committed on its own session
    device = await FleetService(session).get_device(device_id)
    assert device.status is DeviceStatus.ONLINE
    assert device.last_seen_at is not None
    assert str(gateway.presence.status(str(device_id))) == "online"


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

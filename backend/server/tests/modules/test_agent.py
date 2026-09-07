from __future__ import annotations

import pytest
from dqh.svc_core.contracts.errors import ConflictError

from app.modules.agent.domain import DeviceStatus
from app.modules.agent.schemas import DeviceCreate, HeartbeatIn
from app.modules.agent.service import AgentService
from app.modules.observability.domain import AlertType
from app.modules.observability.repository import AlertRepository


@pytest.fixture
def payload() -> DeviceCreate:
    return DeviceCreate(name="cam-01", site="Plant A", hardware="Jetson Orin Nano")


async def test_register_device_is_provisioning(session, payload):
    device = await AgentService(session).register_device(payload)
    assert device.id is not None
    assert device.status is DeviceStatus.PROVISIONING


async def test_duplicate_name_conflicts(session, payload):
    svc = AgentService(session)
    await svc.register_device(payload)
    with pytest.raises(ConflictError):
        await svc.register_device(payload)


async def test_healthy_heartbeat_marks_online(session, payload):
    svc = AgentService(session)
    device = await svc.register_device(payload)
    device, _ = await svc.record_heartbeat(device.id, HeartbeatIn(inference_latency_ms=12.0))
    assert device.status is DeviceStatus.ONLINE


async def test_slow_heartbeat_degrades_and_raises_alert(session, payload):
    svc = AgentService(session)
    device = await svc.register_device(payload)
    device, _ = await svc.record_heartbeat(device.id, HeartbeatIn(inference_latency_ms=250.0))
    assert device.status is DeviceStatus.DEGRADED

    alerts = await AlertRepository(session).list()
    assert any(a.type is AlertType.LATENCY_DEGRADED for a in alerts)

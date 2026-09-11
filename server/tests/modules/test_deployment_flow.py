from __future__ import annotations

import pytest
from dqh.svc_core.contracts.errors import NotFoundError

from app.core.events import event_bus
from app.core.fleet import fleet
from app.modules.agent.schemas import DeviceCreate, HeartbeatIn
from app.modules.agent.service import AgentService
from app.modules.deployment.event import DeployRequested
from app.modules.deployment.schemas import DeployRequest
from app.modules.deployment.service import DeployService
from app.modules.model_registry.schemas import ModelImage

_IMAGE = ModelImage(
    name="ai-edge-ops-model",
    tag="1.0.0",
    ref="ghcr.io/acme/ai-edge-ops-model:1.0.0",
    digest="sha256:abc",
)
_PINNED = "ghcr.io/acme/ai-edge-ops-model@sha256:abc"


class _FakeCatalog:
    async def get_model(self, tag: str, *, refresh: bool = False) -> ModelImage:
        if tag not in ("1.0.0", _IMAGE.ref):
            raise NotFoundError(f"no such image {tag!r}")
        return _IMAGE


@pytest.fixture(autouse=True)
def _catalog(monkeypatch):
    monkeypatch.setattr("app.modules.deployment.service.model_catalog", _FakeCatalog())


async def _device(session):
    return await AgentService(session).register_device(
        DeviceCreate(device_id="cam-01", name="cam-01", site="A")
    )


async def test_deploy_rejects_image_not_in_registry(session):
    await _device(session)
    with pytest.raises(NotFoundError):
        await DeployService(session).deploy(DeployRequest(device_id="cam-01", image="9.9.9"))


async def test_deploy_sets_desired_image_and_fires_event(session):
    await _device(session)
    events: list = []
    event_bus.subscribe(DeployRequested, lambda e: events.append(e))

    view = await DeployService(session).deploy(DeployRequest(device_id="cam-01", image="1.0.0"))

    assert view.desired_image == _PINNED
    assert view.in_sync is False
    assert (await AgentService(session).get_device("cam-01")).desired_image == _PINNED
    assert events and events[-1].image == _PINNED


async def test_in_sync_once_the_device_reports_the_image(session):
    await _device(session)
    await DeployService(session).deploy(DeployRequest(device_id="cam-01", image="1.0.0"))
    fleet.record_heartbeat("cam-01", HeartbeatIn(active_image=_PINNED))

    listed = await DeployService(session).list()
    assert listed[0].in_sync is True
    assert await DeployService(session).count_active() == 1


async def test_config_resolver_layers_model_then_policy_then_device(session):
    await _device(session)
    from app.modules.deployment.config_resolver import ConfigResolver
    from app.modules.system.service import SystemService

    _IMAGE.conf = 0.25
    _IMAGE.iou = 0.5
    _IMAGE.classes = ["helmet", "vest"]
    await SystemService(session).update_settings({"inference_policy": {"conf_threshold": 0.4}})
    device = await AgentService(session).get_device("cam-01")
    device.inference = {"imgsz": 960}

    eff = await ConfigResolver(session).resolve(_IMAGE, device)
    assert eff == {
        "conf_threshold": 0.4,   # policy overrides the model default 0.25
        "iou_threshold": 0.5,    # model default, untouched
        "imgsz": 960,            # per-device override
        "classes": ["helmet", "vest"],
    }
    _IMAGE.conf = _IMAGE.iou = None
    _IMAGE.classes = []

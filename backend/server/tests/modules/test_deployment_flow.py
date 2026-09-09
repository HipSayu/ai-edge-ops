from __future__ import annotations

import httpx
import pytest
from dqh.svc_core.contracts.errors import NotFoundError

from app.modules.agent.schemas import DeviceCreate
from app.modules.agent.service import AgentService
from app.modules.deployment.rules import DeploymentStatus
from app.modules.deployment.schemas import DeploymentCreate
from app.modules.deployment.service import DeploymentService
from app.modules.model_registry.catalog import ModelImage

_IMAGE = ModelImage(
    name="ai-edge-ops-model",
    tag="1.0.0",
    ref="ghcr.io/acme/ai-edge-ops-model:1.0.0",
    digest="sha256:abc",
    task="detect",
)


class _FakeCatalog:
    async def get_model(self, tag: str, *, refresh: bool = False) -> ModelImage:
        if tag not in ("1.0.0", _IMAGE.ref):
            raise httpx.HTTPStatusError("404", request=httpx.Request("GET", "x"), response=httpx.Response(404))
        return _IMAGE


@pytest.fixture(autouse=True)
def _catalog(monkeypatch):
    monkeypatch.setattr("app.modules.deployment.service.model_catalog", _FakeCatalog())


async def _device(session):
    return await AgentService(session).register_device(
        DeviceCreate(name="cam-01", site="A", hardware="Orin")
    )


async def test_deploy_rejects_image_not_in_registry(session):
    device = await _device(session)
    with pytest.raises(NotFoundError):
        await DeploymentService(session).create(
            DeploymentCreate(device_id=device.id, image="9.9.9")
        )


async def test_deploy_stores_the_digest_pinned_ref(session):
    device = await _device(session)
    d = await DeploymentService(session).create(
        DeploymentCreate(device_id=device.id, image="1.0.0")
    )
    assert d.image == "ghcr.io/acme/ai-edge-ops-model@sha256:abc"


async def test_activate_supersedes_previous(session):
    device = await _device(session)
    svc = DeploymentService(session)

    first = await svc.create(
        DeploymentCreate(device_id=device.id, image="1.0.0", activate_now=True)
    )
    second = await svc.create(
        DeploymentCreate(device_id=device.id, image="1.0.0", activate_now=True)
    )

    assert (await svc.get(first.id)).status is DeploymentStatus.SUPERSEDED
    assert (await svc.get(second.id)).status is DeploymentStatus.ACTIVE
    assert await svc.count_active() == 1

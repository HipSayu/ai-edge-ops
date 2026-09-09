from __future__ import annotations

import pytest
from dqh.svc_core.contracts.errors import BadRequestError as BusinessRuleError

from app.modules.agent.schemas import DeviceCreate
from app.modules.agent.service import AgentService
from app.modules.deployment.rules import DeploymentStatus
from app.modules.deployment.schemas import DeploymentCreate
from app.modules.deployment.service import DeploymentService
from app.modules.model_registry.rules import ModelFormat, ModelTask, ModelVersionStatus
from app.modules.model_registry.schemas import ModelCreate, ModelVersionCreate
from app.modules.model_registry.service import ModelRegistryService


async def _published_version(session):
    reg = ModelRegistryService(session)
    model = await reg.create_model(
        ModelCreate(name="ppe", task=ModelTask.DETECTION, architecture="yolo26-n")
    )
    version = await reg.add_version(
        model.id,
        ModelVersionCreate(
            version="1.0.0",
            format=ModelFormat.TENSORRT,
            image_repo="reg/models/ppe",
            image_cpu_digest="sha256:abc",
        ),
    )
    await reg.transition_version(version.id, ModelVersionStatus.VALIDATED)
    await reg.transition_version(version.id, ModelVersionStatus.PUBLISHED)
    return version


async def test_cannot_deploy_unpublished_version(session):
    reg = ModelRegistryService(session)
    model = await reg.create_model(
        ModelCreate(name="ppe", task=ModelTask.DETECTION, architecture="yolo26-n")
    )
    version = await reg.add_version(
        model.id,
        ModelVersionCreate(
            version="0.1.0",
            format=ModelFormat.ONNX,
            image_repo="reg/models/ppe",
            image_cpu_digest="sha256:old",
        ),
    )
    device = await AgentService(session).register_device(
        DeviceCreate(name="cam-01", site="A", hardware="Orin")
    )
    with pytest.raises(BusinessRuleError):
        await DeploymentService(session).create(
            DeploymentCreate(device_id=device.id, model_version_id=version.id)
        )


async def test_activate_supersedes_previous(session):
    version = await _published_version(session)
    device = await AgentService(session).register_device(
        DeviceCreate(name="cam-01", site="A", hardware="Orin")
    )
    svc = DeploymentService(session)

    first = await svc.create(
        DeploymentCreate(device_id=device.id, model_version_id=version.id, activate_now=True)
    )
    second = await svc.create(
        DeploymentCreate(device_id=device.id, model_version_id=version.id, activate_now=True)
    )

    assert (await svc.get(first.id)).status is DeploymentStatus.SUPERSEDED
    assert (await svc.get(second.id)).status is DeploymentStatus.ACTIVE
    assert await svc.count_active() == 1

import pytest

from src.edge.application.services.runtime_containers import RuntimeContainers
from src.edge.application.services.runtime_service import RuntimeService
from src.shared.contracts import RuntimeSpec, RuntimeStatus
from src.shared.exceptions import AppException, ErrorCode
from tests.fakes.edge.fake_container_engine import FakeContainerEngine

SPEC = RuntimeSpec(runtime_id="rt000001", name="ppe", image_uri="nginx", image_tag="1.27-alpine")
RID = SPEC.runtime_id


@pytest.fixture
def engine() -> FakeContainerEngine:
    return FakeContainerEngine()


@pytest.fixture
def service(engine) -> RuntimeService:
    return RuntimeService(engine, RuntimeContainers("node-a"), fetcher=None)


async def test_lifecycle_drives_the_container(engine, service):
    instance = await service.apply(SPEC)
    name = instance.container_id
    assert instance.status == RuntimeStatus.RUNNING and engine.containers[name].running

    assert (await service.stop(RID)).status == RuntimeStatus.STOPPED and not engine.containers[name].running
    assert (await service.start(RID)).status == RuntimeStatus.RUNNING and engine.containers[name].running
    assert (await service.restart(RID)).status == RuntimeStatus.RUNNING
    assert engine.containers[name].restart_count == 1

    await service.remove(RID)
    assert name not in engine.containers and service.list() == []


async def test_redeploying_the_same_spec_keeps_the_container(engine, service):
    await service.apply(SPEC)
    engine.pulled.clear()
    await service.apply(SPEC)
    assert engine.pulled == []  # no pull, no re-create

    await service.apply(SPEC.model_copy(update={"image_tag": "1.28-alpine"}))
    assert engine.pulled == ["nginx:1.28-alpine"]


async def test_reconcile_reports_crashes_and_recovery(engine, service):
    instance = await service.apply(SPEC)
    engine.crash(instance.container_id, exit_code=137)
    await service.reconcile()
    assert instance.status == RuntimeStatus.FAILED and instance.message == "exited with code 137"

    engine.crash(instance.container_id, restarting=True)
    await service.reconcile()
    assert instance.status == RuntimeStatus.RESTARTING

    await engine.start(instance.container_id)
    await service.reconcile()
    assert instance.status == RuntimeStatus.RUNNING and instance.message is None


async def test_reconcile_relaunches_a_vanished_container(engine, service):
    instance = await service.apply(SPEC)
    engine.vanish(instance.container_id)
    await service.reconcile()
    assert instance.status == RuntimeStatus.RUNNING and instance.container_id in engine.containers


async def test_reconcile_leaves_a_stopped_runtime_stopped(engine, service):
    instance = await service.apply(SPEC)
    await service.stop(RID)
    engine.vanish(instance.container_id)
    await service.reconcile()
    assert instance.status == RuntimeStatus.STOPPED and engine.containers == {}


async def test_start_relaunches_when_the_container_is_gone(engine, service):
    instance = await service.apply(SPEC)
    await service.stop(RID)
    engine.vanish(instance.container_id)
    assert (await service.start(RID)).status == RuntimeStatus.RUNNING
    assert instance.container_id in engine.containers


async def test_engine_down_marks_the_runtime_failed(engine, service):
    await service.apply(SPEC)
    engine.reachable = False
    with pytest.raises(AppException) as err:
        await service.restart(RID)
    assert err.value.code == ErrorCode.EXTERNAL_SERVICE
    assert service.get(RID).status == RuntimeStatus.FAILED

    await service.reconcile()  # engine still down: skipped, no crash

from hopquangdo.containers import ContainerState

from src.edge.application.services.runtime_containers import (
    NODE_LABEL,
    RUNTIME_LABEL,
    SPEC_LABEL,
    RuntimeContainers,
)
from src.edge.application.services.runtime_service import RuntimeService
from src.shared.contracts import RuntimeSpec, RuntimeStatus
from tests.fakes.edge.fake_container_engine import FakeContainerEngine

SPEC = RuntimeSpec(runtime_id="rt000001", name="ppe", image_uri="nginx", image_tag="1.27-alpine")


def _service(engine: FakeContainerEngine, node_id: str = "node-a") -> RuntimeService:
    return RuntimeService(engine, RuntimeContainers(node_id), fetcher=None)


def _container(name: str, image: str, status: str, labels: dict | None = None) -> ContainerState:
    return ContainerState(id=name, name=name, image=image, labels={RUNTIME_LABEL: "rt-1", **(labels or {})},
                          running=status == "running", status=status)


def test_adopts_labelled_and_legacy_containers():
    spec = RuntimeSpec(runtime_id="rt-1", name="ppe-detector", image_uri="ghcr.io/x/ppe", image_tag="v2",
                       config={"fps": 15})
    labelled = RuntimeContainers.to_managed(
        _container("edgeops-ppe-detector-rt1abcde", "ghcr.io/x/ppe:v2", "running", {SPEC_LABEL: spec.model_dump_json()})
    )
    assert labelled.spec == spec and labelled.desired_running

    legacy = RuntimeContainers.to_managed(_container("edgeops-ppe-detector-aaf04507", "nginx:1.27-alpine", "exited"))
    assert (legacy.spec.name, legacy.spec.image_uri, legacy.spec.image_tag) == ("ppe-detector", "nginx", "1.27-alpine")
    assert legacy.container_id == "edgeops-ppe-detector-aaf04507" and not legacy.desired_running


def test_container_spec_carries_limits_and_ownership():
    spec = SPEC.model_copy(update={"resource_limits": {"cpus": "100m", "memory": "64Mi", "gpus": 1}})
    container = RuntimeContainers("node-a").to_container(spec, {"A": 1}, {"/host/m.pt": "/models/m.pt"})
    assert container.name == "edgeops-ppe-rt000001"
    assert container.labels[RUNTIME_LABEL] == "rt000001" and container.labels[NODE_LABEL] == "node-a"
    assert (container.cpus, container.memory, container.gpus, container.env) == ("100m", "64Mi", 1, {"A": "1"})


async def test_restore_takes_over_only_own_containers():
    engine = FakeContainerEngine()
    await _service(engine, "node-a").apply(SPEC)
    await _service(engine, "node-b").apply(SPEC.model_copy(update={"runtime_id": "rt000002"}))

    restored = _service(engine, "node-a")
    await restored.restore()
    assert [i.runtime_id for i in restored.list()] == ["rt000001"]
    assert restored.get("rt000001").status == RuntimeStatus.RUNNING


async def test_restore_without_engine_starts_empty():
    service = _service(FakeContainerEngine(reachable=False))
    await service.restore()
    assert service.snapshot() == []

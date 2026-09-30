import pytest

from src.cloud.application.services.entity_resolver import EntityResolver, match, normalize
from src.cloud.domain.entities.cluster import Cluster
from src.cloud.domain.entities.deployment import Deployment
from src.cloud.domain.entities.node import Node
from src.cloud.domain.entities.runtime import Runtime
from src.shared.exceptions import AppException, ErrorCode
from tests.fakes.cloud.fake_cloud_repositories import FakeCloudRepositories


def test_normalize_ignores_case_diacritics_and_spacing():
    assert normalize("  Công  Trường Đường ") == "cong truong duong"


def test_match_prefers_exact_tiers_over_partial_names():
    names = ["Hố móng", "Hố móng phụ"]
    found = match("ho mong", names, id_of=lambda n: n, name_of=lambda n: n)
    assert found == ["Hố móng"]  # the exact name wins over "contains"
    assert match("phu", names, id_of=lambda n: n, name_of=lambda n: n) == ["Hố móng phụ"]
    assert match("phu", names, id_of=lambda n: n, name_of=lambda n: n, exact=True) == []


@pytest.fixture
async def resolver():
    repos = FakeCloudRepositories.create()
    await repos.clusters.add(Cluster(id="c1", name="Công trường A", metadata={"site_code": "CT-A"}))
    await repos.clusters.add(Cluster(id="c2", name="Công trường B", metadata={"site_code": "CT-B"}))
    await repos.nodes.add(Node(id="n1", cluster_id="c1", name="Hố móng", metadata={"code": "CT-A-01"}))
    await repos.nodes.add(Node(id="n2", cluster_id="c2", name="Cẩu tháp"))
    await repos.nodes.add(Node(id="n3", cluster_id="c2", name="Hố móng"))
    await repos.runtimes.add(Runtime(id="r1", node_id="n1", name="ppe-detector"))
    await repos.runtimes.add(Runtime(id="r2", node_id="n2", name="ppe-detector"))
    await repos.deployments.add(Deployment(id="d1", cluster_id="c1", node_id="n1", runtime_id="r1", spec={}))
    return EntityResolver(repos.clusters, repos.nodes, repos.runtimes, repos.deployments)


async def test_cluster_by_id_code_or_name(resolver):
    assert (await resolver.cluster("c1")).id == "c1"
    assert (await resolver.cluster("ct-b")).id == "c2"
    assert (await resolver.cluster("cong truong a")).id == "c1"


async def test_node_scoped_by_cluster(resolver):
    assert (await resolver.node("CT-A-01")).id == "n1"
    assert (await resolver.node("CT-B/Hố móng")).id == "n3"
    assert (await resolver.node("hố móng", cluster="Công trường A")).id == "n1"
    with pytest.raises(AppException) as err:
        await resolver.node("Hố móng")
    assert err.value.code == ErrorCode.INVALID_REQUEST and len(err.value.details["candidates"]) == 2


async def test_not_found_lists_what_exists(resolver):
    with pytest.raises(AppException) as err:
        await resolver.node("Tầng hầm", cluster="CT-A")
    assert err.value.code == ErrorCode.NOT_FOUND and "Hố móng" in err.value.message


async def test_runtime_and_deployment_by_name_within_node(resolver):
    with pytest.raises(AppException):
        await resolver.runtime("ppe-detector")  # on two nodes
    assert (await resolver.runtime("ppe-detector", node="CT-A-01")).id == "r1"
    assert (await resolver.runtime("Cẩu tháp/ppe-detector")).id == "r2"
    assert (await resolver.deployment("ppe-detector", node="Hố móng", cluster="CT-A")).id == "d1"
    assert (await resolver.deployment("d1")).id == "d1"


async def test_exact_refuses_partial_names(resolver):
    assert (await resolver.node("cau", cluster="CT-B")).id == "n2"
    with pytest.raises(AppException):
        await resolver.node("cau", cluster="CT-B", exact=True)

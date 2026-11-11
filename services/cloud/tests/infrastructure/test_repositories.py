"""The repositories keep their promises: domain objects in and out, ids assigned, cascades honoured."""

from datetime import UTC, datetime, timedelta

import pytest

from cloud.domain.model.cluster import Cluster
from cloud.domain.model.node import Node
from cloud.domain.model.user import User
from cloud.domain.violation.violation_event import ViolationEvent
from cloud.infrastructure.persistence.database import create_engine_for, create_schema, make_session_factory
from cloud.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from shared.roles import Role


@pytest.fixture
def uow(tmp_path):
    engine = create_engine_for(f"sqlite:///{(tmp_path / 'repo.db').as_posix()}")
    create_schema(engine)
    factory = make_session_factory(engine)
    yield lambda: SqlAlchemyUnitOfWork(factory)
    engine.dispose()


def make_node(uow, cameras=("A", "B")) -> Node:
    with uow() as u:
        cluster = u.clusters.add(Cluster(name="Site"))
        node = Node(cluster_id=cluster.id, name="N", max_cameras=4)
        for name in cameras:
            node.add_camera(name)
        return u.nodes.add(node)


def test_adding_a_node_assigns_ids_to_it_and_its_cameras(uow):
    node = make_node(uow)
    assert node.id is not None
    assert all(c.id is not None for c in node.cameras)


def test_node_round_trip_keeps_cameras_in_order(uow):
    node = make_node(uow, cameras=("A", "B", "C"))
    with uow() as u:
        assert [c.name for c in u.nodes.get(node.id).cameras] == ["A", "B", "C"]


def test_saving_a_node_adds_changes_and_removes_cameras(uow):
    node = make_node(uow, cameras=("A", "B"))
    with uow() as u:
        loaded = u.nodes.get(node.id)
        loaded.remove_camera(loaded.cameras[0].id)
        loaded.cameras[0].update(name="B2")
        new = loaded.add_camera("C")
        u.nodes.save(loaded)
        assert new.id is not None
    with uow() as u:
        assert [c.name for c in u.nodes.get(node.id).cameras] == ["B2", "C"]


def test_node_found_by_one_of_its_cameras(uow):
    node = make_node(uow)
    with uow() as u:
        assert u.nodes.get_by_camera(node.cameras[1].id).id == node.id
        assert u.nodes.get_by_camera(9999) is None


def test_deleting_a_cluster_removes_nodes_cameras_and_events(uow):
    node = make_node(uow)
    camera_id = node.cameras[0].id
    with uow() as u:
        u.events.add(ViolationEvent(camera_id=camera_id, violation_type="no_helmet", confidence=0.8))
        u.clusters.remove(node.cluster_id)
    with uow() as u:
        assert u.nodes.get(node.id) is None
        assert u.events.recent({camera_id}) == []


def test_a_failed_block_rolls_everything_back(uow):
    with pytest.raises(RuntimeError):
        with uow() as u:
            u.clusters.add(Cluster(name="Ghost"))
            raise RuntimeError("boom")
    with uow() as u:
        assert u.clusters.by_name("Ghost") is None


def test_user_clusters_are_stored_as_ids(uow):
    with uow() as u:
        cluster = u.clusters.add(Cluster(name="Site"))
        user = u.users.add(User(username="op", password_hash="h", full_name="Op", role=Role.OPERATOR,
                                cluster_ids=[cluster.id]))
    with uow() as u:
        loaded = u.users.by_username("op")
        assert loaded.id == user.id and loaded.cluster_ids == [cluster.id] and loaded.role is Role.OPERATOR


def test_event_queries_filter_by_camera_time_and_type(uow):
    first, second = (c.id for c in make_node(uow, cameras=("A", "B")).cameras)
    now = datetime.now(UTC)
    with uow() as u:
        for camera_id, kind, age in [(first, "no_helmet", 1), (first, "no_vest", 2), (second, "no_helmet", 90)]:
            u.events.add(ViolationEvent(camera_id=camera_id, violation_type=kind, confidence=0.5,
                                        created_at=now - timedelta(minutes=age)))
    with uow() as u:
        both, since = {first, second}, now - timedelta(minutes=10)
        assert u.events.counts_by_type(both, since) == {"no_helmet": 1, "no_vest": 1}
        assert u.events.counts_by_camera(both, since) == {first: 2}
        assert [e.violation_type for e in u.events.recent({first}, since, limit=1)] == ["no_helmet"]
        assert len(u.events.between(both, now - timedelta(hours=2))) == 3
        assert u.events.recent(set()) == []
        assert u.events.recent({first}, limit=0) == []
        assert all(e.created_at.tzinfo is not None for e in u.events.recent({first}))

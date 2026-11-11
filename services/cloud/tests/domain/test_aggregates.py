import pytest

from cloud.domain.model.cluster import Cluster
from cloud.domain.model.node import Node
from cloud.domain.model.user import User
from cloud.domain.violation.violation_event import ViolationEvent
from shared.errors import Conflict, Forbidden, Invalid, NotAllowed
from shared.roles import Role
from shared.viewer import Viewer


def viewer(role: Role, clusters: tuple[int, ...] = ()) -> Viewer:
    return Viewer(id=1, username="u", full_name="U", role=role, cluster_ids=clusters)


# ---- Node aggregate

def test_node_refuses_a_camera_beyond_its_capacity():
    node = Node(cluster_id=1, name="N", max_cameras=1)
    node.add_camera("A")
    with pytest.raises(Conflict):
        node.add_camera("B")
    assert node.camera_count == 1


def test_camera_name_is_trimmed_and_required():
    node = Node(cluster_id=1, name="N")
    assert node.add_camera("  Cổng  ").name == "Cổng"
    with pytest.raises(Invalid):
        node.add_camera("   ")


def test_node_needs_a_name_and_room_for_a_camera():
    with pytest.raises(Invalid):
        Node(cluster_id=1, name=" ")
    with pytest.raises(Invalid):
        Node(cluster_id=1, name="N", max_cameras=0)


def test_node_cannot_move_cluster_while_it_has_cameras():
    node = Node(cluster_id=1, name="N")
    node.add_camera("A")
    with pytest.raises(Conflict):
        node.reconfigure(name="N", cluster_id=2, max_cameras=16, description=None, ip_address=None)


def test_node_cannot_shrink_below_its_cameras():
    node = Node(cluster_id=1, name="N")
    node.add_camera("A")
    node.add_camera("B")
    with pytest.raises(Conflict):
        node.reconfigure(name="N", cluster_id=1, max_cameras=1, description=None, ip_address=None)


def test_unknown_camera_is_not_allowed():
    with pytest.raises(NotAllowed):
        Node(cluster_id=1, name="N").camera(99)


def test_camera_update_applies_only_given_fields():
    node = Node(cluster_id=1, name="N")
    camera = node.add_camera("A", zone="Tầng 1")
    camera.update(enabled=False)
    assert (camera.name, camera.zone, camera.enabled) == ("A", "Tầng 1", False)
    with pytest.raises(Invalid):
        camera.update(node_id=3)  # a camera never moves


# ---- Cluster, User, ViolationEvent

def test_cluster_needs_a_name():
    with pytest.raises(Invalid):
        Cluster(name="")


def test_admin_keeps_no_cluster_assignments():
    user = User(username="a", password_hash="h", full_name="A", role=Role.VIEWER, cluster_ids=[2, 1, 2])
    assert user.cluster_ids == [1, 2]
    user.update_profile(full_name="A", role=Role.ADMIN, is_active=True, cluster_ids=[1])
    assert user.cluster_ids == []


def test_user_becomes_a_viewer_with_its_clusters():
    user = User(id=7, username="a", password_hash="h", full_name="A", role=Role.OPERATOR, cluster_ids=[3])
    assert user.to_viewer() == Viewer(id=7, username="a", full_name="A", role=Role.OPERATOR, cluster_ids=(3,))


def test_violation_event_accepts_only_known_violations():
    assert ViolationEvent(camera_id=1, violation_type="no_helmet", confidence=0.9).id is None
    with pytest.raises(Invalid):
        ViolationEvent(camera_id=1, violation_type="person", confidence=0.9)


# ---- Viewer

def test_viewer_cluster_access():
    assert viewer(Role.ADMIN).can_access_cluster(99)
    assert viewer(Role.VIEWER, (1,)).can_access_cluster(1)
    assert not viewer(Role.VIEWER, (1,)).can_access_cluster(2)


def test_viewer_require_cluster_and_role_raise_forbidden():
    with pytest.raises(Forbidden):
        viewer(Role.OPERATOR, (1,)).require_cluster(2)
    with pytest.raises(Forbidden):
        viewer(Role.VIEWER).require_role(Role.OPERATOR)
    viewer(Role.ADMIN).require_role(Role.OPERATOR)  # ranks above: no error

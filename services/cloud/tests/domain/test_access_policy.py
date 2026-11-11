from cloud.domain.policy.access_policy import allowed_camera_ids
from shared.roles import Role

# (camera_id, cluster_id of its node)
CAMERAS = [(1, 10), (2, 20), (3, 10)]


def test_admin_sees_every_camera():
    assert allowed_camera_ids(Role.ADMIN, set(), CAMERAS) == {1, 2, 3}


def test_viewer_sees_cameras_of_their_clusters_only():
    assert allowed_camera_ids(Role.VIEWER, {10}, CAMERAS) == {1, 3}


def test_operator_with_two_clusters():
    assert allowed_camera_ids(Role.OPERATOR, {10, 20}, CAMERAS) == {1, 2, 3}


def test_no_clusters_means_no_cameras():
    assert allowed_camera_ids(Role.VIEWER, set(), CAMERAS) == set()

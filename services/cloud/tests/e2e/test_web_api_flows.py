"""End-to-end flows the web app drives, one scenario per user journey.

Each test follows what the web does: log in, load the data it shows, then perform the action. The role
matrix is the one in docs/ppe-vision/06-api-tool-spec.md section 1.
"""

import re

import pytest
from fastapi.testclient import TestClient

from cloud.interface.rest.app import create_app
from cloud.bootstrap.settings import Settings


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        data_dir=tmp_path,
        video_dir=tmp_path / "video",
        database_url=f"sqlite:///{(tmp_path / 'e2e.db').as_posix()}",
    )
    with TestClient(create_app(settings)) as c:
        yield c


def login(client, username, password="demo123"):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(client):
    return login(client, "admin", "admin123")


@pytest.fixture
def operator(client):
    return login(client, "operator1")


@pytest.fixture
def viewer(client):
    return login(client, "viewer1")


@pytest.fixture
def world(client, admin):
    """Two clusters. Cluster A holds the seeded node plus one camera; cluster B holds one camera.

    Viewer and operator are assigned to cluster A only (seed), so cluster B is out of their scope.
    """
    cluster_a = client.get("/api/clusters", headers=admin).json()[0]
    node_a = client.get(f"/api/nodes?cluster_id={cluster_a['id']}", headers=admin).json()[0]
    cam_a = client.post("/api/cameras", json={"name": "Cổng A", "node_id": node_a["id"]}, headers=admin).json()

    cluster_b = client.post("/api/clusters", json={"name": "Công trường B"}, headers=admin).json()
    node_b = client.post("/api/nodes", json={"name": "Node B", "cluster_id": cluster_b["id"]}, headers=admin).json()
    cam_b = client.post("/api/cameras", json={"name": "Cổng B", "node_id": node_b["id"]}, headers=admin).json()
    return {"cluster_a": cluster_a, "cluster_b": cluster_b, "cam_a": cam_a, "cam_b": cam_b}


# ---------------------------------------------------------------- 1. login and session

def test_login_then_me_returns_role_and_scope(client, operator, world):
    me = client.get("/api/auth/me", headers=operator).json()
    assert me["username"] == "operator1"
    assert me["role"] == "OPERATOR"
    assert me["cluster_ids"] == [world["cluster_a"]["id"]]


@pytest.mark.parametrize("username,password", [
    ("admin", "wrong"),
    ("nobody", "admin123"),
])
def test_login_rejects_bad_credentials(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 401


def test_requests_without_or_with_bad_token_get_401(client):
    assert client.get("/api/grid").status_code == 401
    assert client.get("/api/grid", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_disabled_account_cannot_login_or_keep_session(client, admin, viewer, world):
    target = client.get("/api/users", headers=admin).json()
    viewer_id = next(u["id"] for u in target if u["username"] == "viewer1")
    body = {"username": "viewer1", "full_name": "Viewer 1", "role": "VIEWER", "is_active": False,
            "cluster_ids": [world["cluster_a"]["id"]]}
    assert client.put(f"/api/users/{viewer_id}", json=body, headers=admin).status_code == 200

    assert client.post("/api/auth/login", json={"username": "viewer1", "password": "demo123"}).status_code == 401
    assert client.get("/api/grid", headers=viewer).status_code == 401


# ---------------------------------------------------------------- 2. role matrix

@pytest.mark.parametrize("who,expected", [("viewer", 403), ("operator", 403), ("admin", 201)])
def test_only_admin_creates_clusters(client, request, who, expected):
    headers = request.getfixturevalue(who)
    assert client.post("/api/clusters", json={"name": "X"}, headers=headers).status_code == expected


@pytest.mark.parametrize("who,expected", [("viewer", 403), ("operator", 403), ("admin", 200)])
def test_only_admin_lists_users(client, request, who, expected):
    headers = request.getfixturevalue(who)
    assert client.get("/api/users", headers=headers).status_code == expected


@pytest.mark.parametrize("who,expected", [("viewer", 403), ("operator", 200)])
def test_operator_can_run_video_sync(client, request, who, expected):
    headers = request.getfixturevalue(who)
    assert client.post("/api/cameras/sync", headers=headers).status_code == expected


def test_viewer_can_read_monitor_but_not_mutate_cameras(client, viewer, admin, world):
    assert client.get("/api/cameras", headers=viewer).status_code == 200
    assert client.get("/api/grid", headers=viewer).status_code == 200
    assert client.get("/api/stats", headers=viewer).status_code == 200
    cam = world["cam_a"]
    body = {"name": "Đổi tên", "enabled": True}
    assert client.put(f"/api/cameras/{cam['id']}", json=body, headers=viewer).status_code == 403
    assert client.delete(f"/api/cameras/{cam['id']}", headers=viewer).status_code == 403


def test_operator_cannot_manage_cameras_or_nodes(client, operator, world):
    cam = world["cam_a"]
    assert client.put(f"/api/cameras/{cam['id']}", json={"name": "x", "enabled": True}, headers=operator).status_code == 403
    assert client.delete(f"/api/cameras/{cam['id']}", headers=operator).status_code == 403
    node = {"name": "N", "cluster_id": world["cluster_a"]["id"]}
    assert client.post("/api/nodes", json=node, headers=operator).status_code == 403


# ---------------------------------------------------------------- 3. cluster scope

def test_viewer_sees_only_assigned_cluster_cameras(client, viewer, world):
    ids = {c["id"] for c in client.get("/api/cameras", headers=viewer).json()}
    assert world["cam_a"]["id"] in ids
    assert world["cam_b"]["id"] not in ids


def test_grid_refuses_cluster_outside_scope(client, viewer, world):
    other = world["cluster_b"]["id"]
    assert client.get(f"/api/grid?cluster_id={other}", headers=viewer).status_code == 403


def test_grid_only_lists_visible_cameras(client, viewer, world):
    cams = {item["camera_id"] for item in client.get("/api/grid", headers=viewer).json()}
    assert cams == {world["cam_a"]["id"]}


def test_stats_refuses_cluster_outside_scope(client, viewer, world):
    other = world["cluster_b"]["id"]
    assert client.get(f"/api/stats?cluster_id={other}", headers=viewer).status_code == 403


def test_admin_sees_all_clusters_and_cameras(client, admin, world):
    cams = {item["camera_id"] for item in client.get("/api/grid", headers=admin).json()}
    assert {world["cam_a"]["id"], world["cam_b"]["id"]} <= cams


def test_out_of_scope_camera_is_hidden_as_404(client, viewer, world):
    hidden = world["cam_b"]["id"]
    assert client.get(f"/api/cameras/{hidden}/events", headers=viewer).status_code == 404
    assert client.get(f"/api/cameras/{hidden}/stream", headers=viewer).status_code == 404


def test_disabled_camera_stream_is_404(client, admin, world):
    cam = world["cam_a"]
    client.put(f"/api/cameras/{cam['id']}", json={"name": cam["name"], "enabled": False}, headers=admin)
    assert client.get(f"/api/cameras/{cam['id']}/stream", headers=admin).status_code == 404


# ---------------------------------------------------------------- 4. media (token in query)

def test_media_wants_the_header_and_ignores_a_token_in_the_url(client, viewer, world):
    token = viewer["Authorization"].split()[1]
    assert client.get(f"/api/cameras/{world['cam_b']['id']}/stream", headers=viewer).status_code == 404
    assert client.get("/api/snapshots/999", headers=viewer).status_code == 404
    assert client.get(f"/api/cameras/{world['cam_b']['id']}/stream?token={token}").status_code == 401
    assert client.get(f"/api/snapshots/999?token={token}").status_code == 401


def test_media_without_token_is_401(client, world):
    assert client.get(f"/api/cameras/{world['cam_a']['id']}/stream").status_code == 401
    assert client.get("/api/snapshots/1").status_code == 401


def test_snapshot_of_unknown_event_is_404(client, viewer):
    assert client.get("/api/snapshots/999", headers=viewer).status_code == 404


# ---------------------------------------------------------------- 5. CRUD round trips the web performs

def test_cluster_node_camera_crud_round_trip(client, admin, world):
    cluster = client.post("/api/clusters", json={"name": "Mới", "description": "d"}, headers=admin).json()
    assert client.put(f"/api/clusters/{cluster['id']}", json={"name": "Mới 2"}, headers=admin).json()["name"] == "Mới 2"

    node = client.post("/api/nodes", json={"name": "N", "cluster_id": cluster["id"], "max_cameras": 2},
                       headers=admin).json()
    assert client.put(f"/api/nodes/{node['id']}", json={"name": "N2", "cluster_id": cluster["id"], "max_cameras": 3},
                      headers=admin).json()["max_cameras"] == 3

    cam = client.post("/api/cameras", json={"name": "C", "node_id": node["id"]}, headers=admin).json()
    assert client.delete(f"/api/cameras/{cam['id']}", headers=admin).status_code == 204
    assert client.delete(f"/api/nodes/{node['id']}", headers=admin).status_code == 204
    assert client.delete(f"/api/clusters/{cluster['id']}", headers=admin).status_code == 204


def test_user_assigned_to_new_cluster_gains_access(client, admin, world):
    body = {"username": "op2", "password": "pw-op2", "full_name": "Op 2", "role": "OPERATOR",
            "cluster_ids": [world["cluster_b"]["id"]]}
    created = client.post("/api/users", json=body, headers=admin)
    assert created.status_code == 201
    headers = login(client, "op2", "pw-op2")
    assert client.get("/api/auth/me", headers=headers).json()["cluster_ids"] == [world["cluster_b"]["id"]]
    ids = {c["id"] for c in client.get("/api/cameras", headers=headers).json()}
    assert ids == {world["cam_b"]["id"]}


def test_deleted_user_loses_session(client, admin, world):
    body = {"username": "tmp", "password": "pw-tmp", "full_name": "Tạm", "role": "VIEWER", "cluster_ids": []}
    uid = client.post("/api/users", json=body, headers=admin).json()["id"]
    headers = login(client, "tmp", "pw-tmp")
    assert client.delete(f"/api/users/{uid}", headers=admin).status_code == 204
    assert client.get("/api/grid", headers=headers).status_code == 401


def test_duplicate_username_is_409(client, admin):
    body = {"username": "admin", "password": "x", "full_name": "x", "role": "ADMIN"}
    assert client.post("/api/users", json=body, headers=admin).status_code == 409


def test_invalid_role_is_400(client, admin):
    body = {"username": "bad", "password": "x", "full_name": "x", "role": "SUPERUSER"}
    assert client.post("/api/users", json=body, headers=admin).status_code == 400


# ---------------------------------------------------------------- 6. web contract

WEB_CALLS = [
    ("POST", "/api/auth/login"), ("GET", "/api/auth/me"),
    ("GET", "/api/clusters"), ("POST", "/api/clusters"), ("PUT", "/api/clusters/{id}"), ("DELETE", "/api/clusters/{id}"),
    ("GET", "/api/nodes"), ("POST", "/api/nodes"), ("PUT", "/api/nodes/{id}"), ("DELETE", "/api/nodes/{id}"),
    ("GET", "/api/cameras"), ("PUT", "/api/cameras/{id}"), ("DELETE", "/api/cameras/{id}"),
    ("POST", "/api/cameras/upload"), ("POST", "/api/cameras/sync"), ("GET", "/api/cameras/{id}/events"),
    ("GET", "/api/cameras/{id}/stream"), ("GET", "/api/snapshots/{id}"),
    ("GET", "/api/grid"), ("GET", "/api/stats"),
    ("GET", "/api/cameras/{id}/status"), ("GET", "/api/violations"),
    ("GET", "/api/violations/{id}/frame"), ("GET", "/api/analytics/trend"),
    ("GET", "/api/analytics/rank"), ("GET", "/api/analytics/compare"),
    ("GET", "/api/users"), ("POST", "/api/users"), ("PUT", "/api/users/{id}"), ("DELETE", "/api/users/{id}"),
]


def test_every_path_the_web_calls_exists_in_openapi(client):
    spec = client.get("/openapi.json").json()
    served = set()
    for path, ops in spec["paths"].items():
        for method in ops:
            served.add((method.upper(), path.replace("/api/v1", "/api", 1)))  # the web still calls the unversioned alias
    normalise = lambda p: re.sub(r"\{[^}]+\}", "{x}", p)
    served_norm = {(m, normalise(p)) for m, p in served}
    missing = [(m, p) for m, p in WEB_CALLS if (m, normalise(p)) not in served_norm]
    assert not missing, f"web calls with no backend route: {missing}"

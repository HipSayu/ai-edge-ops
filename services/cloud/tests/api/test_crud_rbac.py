import pytest
from fastapi.testclient import TestClient

from cloud.interface.rest.app import create_app
from cloud.bootstrap.settings import Settings


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        data_dir=tmp_path,
        video_dir=tmp_path / "video",
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
    )
    with TestClient(create_app(settings)) as c:
        yield c


def login(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(client):
    return login(client, "admin", "admin123")


@pytest.fixture
def operator(client):
    return login(client, "operator1", "demo123")


@pytest.fixture
def viewer(client):
    return login(client, "viewer1", "demo123")


@pytest.fixture
def cluster_a(client, admin):
    """The seeded cluster and its seeded node."""
    cluster = client.get("/api/clusters", headers=admin).json()[0]
    node = client.get(f"/api/nodes?cluster_id={cluster['id']}", headers=admin).json()[0]
    return cluster, node


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_login_wrong_password(client):
    assert client.post("/api/auth/login", json={"username": "admin", "password": "nope"}).status_code == 401


def test_protected_route_needs_token(client):
    assert client.get("/api/cameras").status_code == 401


def test_me_returns_clusters(client, operator, cluster_a):
    me = client.get("/api/auth/me", headers=operator).json()
    assert me["role"] == "OPERATOR"
    assert me["cluster_ids"] == [cluster_a[0]["id"]]


def test_cluster_crud_admin_only(client, admin, viewer):
    assert client.post("/api/clusters", json={"name": "Công trường C"}, headers=viewer).status_code == 403
    created = client.post("/api/clusters", json={"name": "Công trường C"}, headers=admin)
    assert created.status_code == 201
    cid = created.json()["id"]
    assert client.put(f"/api/clusters/{cid}", json={"name": "C2"}, headers=admin).json()["name"] == "C2"
    assert client.delete(f"/api/clusters/{cid}", headers=admin).status_code == 204


def test_viewer_sees_only_own_clusters(client, admin, viewer, cluster_a):
    client.post("/api/clusters", json={"name": "Khác"}, headers=admin)
    names = [c["name"] for c in client.get("/api/clusters", headers=viewer).json()]
    assert names == [cluster_a[0]["name"]]


def test_node_crud(client, admin, viewer, cluster_a):
    cluster, _ = cluster_a
    assert client.post("/api/nodes", json={"name": "N2", "cluster_id": cluster["id"]}, headers=viewer).status_code == 403
    created = client.post("/api/nodes", json={"name": "N2", "cluster_id": cluster["id"], "max_cameras": 4}, headers=admin)
    assert created.status_code == 201
    assert created.json()["max_cameras"] == 4
    assert client.post("/api/nodes", json={"name": "x", "cluster_id": 999}, headers=admin).status_code == 404


def test_camera_belongs_to_node_and_respects_limit(client, admin, cluster_a):
    _, node = cluster_a
    small = client.post("/api/nodes", json={"name": "Small", "cluster_id": cluster_a[0]["id"], "max_cameras": 1},
                        headers=admin).json()
    assert client.post("/api/cameras", json={"name": "C1", "node_id": small["id"]}, headers=admin).status_code == 201
    assert client.post("/api/cameras", json={"name": "C2", "node_id": small["id"]}, headers=admin).status_code == 409


def test_camera_visibility_follows_cluster(client, admin, viewer, cluster_a):
    _, node = cluster_a
    cam = client.post("/api/cameras", json={"name": "Cổng", "node_id": node["id"]}, headers=admin).json()
    other_cluster = client.post("/api/clusters", json={"name": "Khác"}, headers=admin).json()
    other_node = client.post("/api/nodes", json={"name": "N", "cluster_id": other_cluster["id"]}, headers=admin).json()
    hidden = client.post("/api/cameras", json={"name": "Kho", "node_id": other_node["id"]}, headers=admin).json()

    visible_ids = [c["id"] for c in client.get("/api/cameras", headers=viewer).json()]
    assert cam["id"] in visible_ids
    assert hidden["id"] not in visible_ids
    assert client.get(f"/api/cameras/{hidden['id']}/events", headers=viewer).status_code == 404


def test_camera_update_keeps_node(client, admin, cluster_a):
    _, node = cluster_a
    cam = client.post("/api/cameras", json={"name": "Cổng", "node_id": node["id"]}, headers=admin).json()
    updated = client.put(f"/api/cameras/{cam['id']}", json={"name": "Cổng 2", "zone": "Tầng 1", "enabled": True},
                         headers=admin).json()
    assert updated["name"] == "Cổng 2"
    assert updated["node_id"] == node["id"]


def test_upload_goes_into_cluster_node_camera_folder(client, operator, admin, cluster_a, tmp_path):
    cluster, node = cluster_a
    cam = client.post("/api/cameras", json={"name": "Cổng", "node_id": node["id"]}, headers=admin).json()
    r = client.post(
        f"/api/cameras/{cam['id']}/videos",
        files={"file": ("walk.mp4", b"fake", "video/mp4")},
        headers=operator,
    )
    assert r.status_code == 201
    expected = tmp_path / "video" / str(cluster["id"]) / str(node["id"]) / str(cam["id"]) / "walk.mp4"
    assert expected.is_file()
    assert r.json()["videos"] == ["walk.mp4"]


def test_upload_rejects_non_video_and_out_of_scope_camera(client, operator, admin, cluster_a):
    _, node = cluster_a
    cam = client.post("/api/cameras", json={"name": "Cổng", "node_id": node["id"]}, headers=admin).json()
    bad = client.post(f"/api/cameras/{cam['id']}/videos", files={"file": ("n.txt", b"x", "text/plain")}, headers=operator)
    assert bad.status_code == 400

    other = client.post("/api/clusters", json={"name": "Khác"}, headers=admin).json()
    other_node = client.post("/api/nodes", json={"name": "N", "cluster_id": other["id"]}, headers=admin).json()
    hidden = client.post("/api/cameras", json={"name": "Kho", "node_id": other_node["id"]}, headers=admin).json()
    r = client.post(f"/api/cameras/{hidden['id']}/videos", files={"file": ("a.mp4", b"x", "video/mp4")}, headers=operator)
    assert r.status_code == 404


def test_sync_creates_missing_folders_and_reports_unmatched(client, operator, admin, cluster_a, tmp_path):
    _, node = cluster_a
    client.post("/api/cameras", json={"name": "Cổng", "node_id": node["id"]}, headers=admin)
    (tmp_path / "video" / "99" / "99" / "99").mkdir(parents=True)  # no camera owns this folder

    report = client.post("/api/cameras/sync", headers=operator).json()
    assert report["cameras"] == 1
    assert report["unmatched_folders"] == ["99/99/99"]


def test_grid_scoped_to_cluster(client, admin, viewer, cluster_a):
    cluster, node = cluster_a
    cam = client.post("/api/cameras", json={"name": "Cổng", "node_id": node["id"]}, headers=admin).json()
    other = client.post("/api/clusters", json={"name": "Khác"}, headers=admin).json()
    assert client.get(f"/api/grid?cluster_id={other['id']}", headers=viewer).status_code == 403
    grid = client.get("/api/grid", headers=viewer).json()
    assert all(item["cluster_id"] == cluster["id"] for item in grid)

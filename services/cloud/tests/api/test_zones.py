"""Forbidden zones over the REST API: who may see and change them, what is accepted, and what the edge is told."""

import pytest
from fastapi.testclient import TestClient

from cloud.interface.rest.app import create_app
from cloud.bootstrap.settings import Settings
from cloud.domain.model.zone import Zone
from edge_link import ZonesMessage
from shared.errors import Invalid
from cloud.infrastructure.messaging.zone_publisher import MqttZonePublisher
from cloud.domain.violation.violation_event import ViolationEvent

SQUARE = [[0.1, 0.1], [0.6, 0.1], [0.6, 0.6], [0.1, 0.6]]


class FakePublisher:
    def __init__(self) -> None:
        self.sent: list[tuple[int, list[Zone]]] = []
        self.accepts = True

    def publish(self, camera_id, zones) -> bool:
        self.sent.append((camera_id, list(zones)))
        return self.accepts


@pytest.fixture
def app_client(tmp_path):
    settings = Settings(
        data_dir=tmp_path, video_dir=tmp_path / "video",
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
    )
    with TestClient(create_app(settings)) as c:
        c.publisher = FakePublisher()
        c.app.state.container.zones._publisher = c.publisher  # the real one needs a broker
        yield c


def login(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(app_client):
    return login(app_client, "admin", "admin123")


@pytest.fixture
def operator(app_client):
    return login(app_client, "operator1", "demo123")


@pytest.fixture
def viewer(app_client):
    return login(app_client, "viewer1", "demo123")


@pytest.fixture
def camera(app_client, admin):
    cluster = app_client.get("/api/clusters", headers=admin).json()[0]
    node = app_client.get(f"/api/nodes?cluster_id={cluster['id']}", headers=admin).json()[0]
    return app_client.post("/api/cameras", json={"name": "Cổng", "node_id": node["id"]}, headers=admin).json()


@pytest.fixture
def hidden_camera(app_client, admin):
    cluster = app_client.post("/api/clusters", json={"name": "Khác"}, headers=admin).json()
    node = app_client.post("/api/nodes", json={"name": "N", "cluster_id": cluster["id"]}, headers=admin).json()
    return app_client.post("/api/cameras", json={"name": "Kho", "node_id": node["id"]}, headers=admin).json()


def put(client, camera, headers, *zones):
    return client.put(f"/api/cameras/{camera['id']}/zones", json={"zones": list(zones)}, headers=headers)


def zone(name="Hố móng", polygon=SQUARE, enabled=True):
    return {"name": name, "polygon": polygon, "enabled": enabled}


def test_a_camera_starts_without_zones(app_client, viewer, camera):
    assert app_client.get(f"/api/cameras/{camera['id']}/zones", headers=viewer).json() == []


def test_an_operator_draws_zones_and_everyone_with_access_sees_them(app_client, operator, viewer, camera):
    r = put(app_client, camera, operator, zone("Hố móng"), zone("Cẩu tháp", enabled=False))
    assert r.status_code == 200
    assert [(z["name"], z["enabled"]) for z in r.json()] == [("Hố móng", True), ("Cẩu tháp", False)]
    assert all(z["id"] for z in r.json())
    seen = app_client.get(f"/api/cameras/{camera['id']}/zones", headers=viewer).json()
    assert [z["name"] for z in seen] == ["Hố móng", "Cẩu tháp"] and seen[0]["polygon"] == SQUARE


def test_a_viewer_may_look_but_not_draw(app_client, viewer, camera):
    assert put(app_client, camera, viewer, zone()).status_code == 403


def test_the_list_replaces_the_zones_so_an_omitted_zone_is_deleted(app_client, operator, camera):
    put(app_client, camera, operator, zone("A"), zone("B"))
    r = put(app_client, camera, operator, zone("B"))
    assert [z["name"] for z in r.json()] == ["B"]
    assert put(app_client, camera, operator).json() == []


def test_a_camera_outside_the_users_clusters_looks_like_it_does_not_exist(app_client, operator, viewer, hidden_camera):
    assert put(app_client, hidden_camera, operator, zone()).status_code == 404
    assert app_client.get(f"/api/cameras/{hidden_camera['id']}/zones", headers=viewer).status_code == 404
    assert app_client.get("/api/cameras/9999/zones", headers=viewer).status_code == 404


@pytest.mark.parametrize("polygon", [
    [[0.1, 0.1], [0.5, 0.5]],                           # two corners
    [[0.1, 0.1], [1.5, 0.1], [0.5, 0.5]],               # outside the picture
    [[0.1, 0.1], [0.3, 0.3], [0.5, 0.5]],               # in a line: no area
])
def test_a_bad_polygon_is_refused_and_nothing_is_saved(app_client, operator, camera, polygon):
    assert put(app_client, camera, operator, zone(polygon=polygon)).status_code == 400
    assert app_client.get(f"/api/cameras/{camera['id']}/zones", headers=operator).json() == []


def test_a_zone_needs_a_name_and_a_camera_a_limit(app_client, operator, camera):
    assert put(app_client, camera, operator, zone(name="  ")).status_code == 400
    assert put(app_client, camera, operator, *[zone(f"z{i}") for i in range(21)]).status_code == 400


def test_the_edge_is_told_after_every_change_with_the_saved_zones(app_client, operator, camera):
    put(app_client, camera, operator, zone("A"))
    put(app_client, camera, operator)
    (first_camera, first), (second_camera, second) = app_client.publisher.sent
    assert first_camera == second_camera == camera["id"]
    assert [z.name for z in first] == ["A"] and first[0].id is not None   # sent with the ids the database gave
    assert second == []                                                   # an empty list clears the camera at the edge


def test_nothing_is_sent_when_the_change_is_refused(app_client, viewer, operator, camera):
    put(app_client, camera, viewer, zone())
    put(app_client, camera, operator, zone(polygon=[[0.1, 0.1], [0.5, 0.5]]))
    assert app_client.publisher.sent == []


def test_a_broker_that_is_down_does_not_undo_the_change(app_client, operator, camera):
    app_client.publisher.accepts = False
    assert put(app_client, camera, operator, zone()).status_code == 200
    assert len(app_client.get(f"/api/cameras/{camera['id']}/zones", headers=operator).json()) == 1


def test_a_publisher_that_raises_does_not_undo_the_change_either(app_client, operator, camera):
    def boom(camera_id, zones):
        raise RuntimeError("broker gone")

    app_client.publisher.publish = boom
    assert put(app_client, camera, operator, zone()).status_code == 200


def test_publish_all_sends_every_camera_that_has_zones(app_client, operator, camera):
    put(app_client, camera, operator, zone("A"))
    app_client.publisher.sent.clear()
    assert app_client.app.state.container.zones.publish_all() == 1
    assert [c for c, _ in app_client.publisher.sent] == [camera["id"]]


def test_the_zones_go_to_the_edge_in_the_wire_format_it_reads(app_client, operator, camera):
    class Client:
        def __init__(self, client_id):
            self.published = []

        def username_pw_set(self, *a):
            pass

        def publish(self, topic, payload, qos=0, retain=False):
            self.published.append((topic, payload, qos, retain))

    clients = []
    publisher = MqttZonePublisher("broker", 1883, client_factory=lambda cid: clients.append(Client(cid)) or clients[0])
    put(app_client, camera, operator, zone("A"))
    zones = app_client.get(f"/api/cameras/{camera['id']}/zones", headers=operator).json()
    assert publisher.publish(camera["id"], [Zone(z["name"], tuple(map(tuple, z["polygon"])), z["enabled"], z["id"]) for z in zones])
    topic, payload, qos, retain = clients[0].published[0]
    assert (topic, qos, retain) == (f"ppe/config/cameras/{camera['id']}/zones", 1, True)
    assert ZonesMessage.parse(payload).zones[0].name == "A"


def test_a_zone_intrusion_is_an_event_type_the_cloud_records():
    assert ViolationEvent(camera_id=1, violation_type="zone_intrusion", confidence=0.9).violation_type == "zone_intrusion"
    with pytest.raises(Invalid):
        ViolationEvent(camera_id=1, violation_type="dancing", confidence=0.9)

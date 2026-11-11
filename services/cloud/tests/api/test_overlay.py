"""The boxes over the video: the server-sent stream of what the edges found, matched to the frame being shown."""

import json
import socket
import threading
import time

import cv2
import httpx
import numpy as np
import pytest
import uvicorn
from edge_link import DetectionBox, DetectionsMessage
from fastapi.testclient import TestClient

from cloud.interface.rest.app import create_app
from cloud.bootstrap.settings import Settings
import struct


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        data_dir=tmp_path, video_dir=tmp_path / "video",
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
    )
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def live(tmp_path):
    """The app on a real local port: a TestClient cannot read a stream that never ends."""
    settings = Settings(
        data_dir=tmp_path, video_dir=tmp_path / "video",
        database_url=f"sqlite:///{(tmp_path / 'live.db').as_posix()}",
    )
    app = create_app(settings)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            if httpx.get(base + "/api/health", timeout=1).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.1)
    yield base, app
    server.should_exit = True
    thread.join(timeout=10)


def make_camera(base, app, tmp_path):
    token = httpx.post(base + "/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
    admin = {"Authorization": f"Bearer {token}"}
    cluster = httpx.get(base + "/api/clusters", headers=admin).json()[0]
    node = httpx.get(base + f"/api/nodes?cluster_id={cluster['id']}", headers=admin).json()[0]
    cam = httpx.post(base + "/api/cameras", headers=admin, json={"node_id": node["id"], "name": "overlay-cam"}).json()
    folder = tmp_path / "video" / str(cluster["id"]) / str(node["id"]) / str(cam["id"])
    folder.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(folder / "v.avi"), cv2.VideoWriter_fourcc(*"MJPG"), 25, (160, 90))
    for i in range(250):
        writer.write(np.full((90, 160, 3), i % 255, np.uint8))
    writer.release()
    return admin, cam["id"]


def events(base, admin, camera_id, count=1, timeout=8.0):
    """The first `count` overlay events of the stream."""
    found = []
    deadline = time.time() + timeout
    with httpx.stream("GET", f"{base}/api/overlay/stream?camera_ids={camera_id}", headers=admin, timeout=timeout) as r:
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
        for line in r.iter_lines():
            if line.startswith("data: "):
                found.append(json.loads(line[6:]))
                if len(found) >= count:
                    break
            assert time.time() < deadline, "no event in time"
    return found


def test_the_stream_sends_the_boxes_of_the_frame_being_shown(live, tmp_path):
    base, app = live
    admin, camera_id = make_camera(base, app, tmp_path)
    store = app.state.container.monitoring._detections
    for tenth in range(100):  # a detection every tenth of a second over the whole video
        store.add(DetectionsMessage("n1", camera_id, tenth / 10, 160, 90, (DetectionBox("no_helmet", 0.9, (1, 2, 30, 40), 4),)))
    for _ in range(40):  # the feed starts with the stream and needs a moment for its first frame
        event = events(base, admin, camera_id)[0]
        if event["boxes"]:
            break
        time.sleep(0.2)
    assert event["camera_id"] == camera_id and event["w"] == 160 and event["h"] == 90
    assert event["boxes"] == [{"l": "no_helmet", "c": 0.9, "b": [1, 2, 30, 40], "t": 4}]


def test_a_camera_without_boxes_gets_an_empty_overlay(live, tmp_path):
    base, app = live
    admin, camera_id = make_camera(base, app, tmp_path)
    assert events(base, admin, camera_id)[0] == {"camera_id": camera_id, "w": 0, "h": 0, "boxes": []}


def test_a_token_in_the_query_is_not_accepted(live, tmp_path):
    base, app = live
    admin, camera_id = make_camera(base, app, tmp_path)
    token = admin["Authorization"].split()[1]
    with httpx.stream("GET", f"{base}/api/overlay/stream?camera_ids={camera_id}&token={token}", timeout=5) as r:
        assert r.status_code == 401


def test_bad_requests_and_strangers_are_refused(client):
    admin = {"Authorization": "Bearer " + client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]}
    assert client.get("/api/overlay/stream?camera_ids=1").status_code == 401
    assert client.get("/api/overlay/stream?camera_ids=abc", headers=admin).status_code == 400
    assert client.get("/api/overlay/stream?camera_ids=", headers=admin).status_code == 400
    assert client.get("/api/overlay/stream?camera_ids=99999", headers=admin).status_code == 404


def read_packets(base, admin, camera_id, count, timeout=10.0):
    """The first `count` packets of /live: (header, jpeg)."""
    found, buf = [], b""
    deadline = time.time() + timeout
    with httpx.stream("GET", f"{base}/api/cameras/{camera_id}/live", headers=admin, timeout=timeout) as r:
        assert r.status_code == 200
        for chunk in r.iter_bytes():
            buf += chunk
            while len(buf) >= 8:
                head_len, jpeg_len = struct.unpack(">II", buf[:8])
                if len(buf) < 8 + head_len + jpeg_len:
                    break
                found.append((json.loads(buf[8:8 + head_len]), buf[8 + head_len:8 + head_len + jpeg_len]))
                buf = buf[8 + head_len + jpeg_len:]
            if len(found) >= count:
                return found
            assert time.time() < deadline, "no packet in time"
    return found


def test_live_sends_each_frame_with_the_boxes_found_on_it(live, tmp_path):
    base, app = live
    admin, camera_id = make_camera(base, app, tmp_path)
    store = app.state.container.monitoring._detections
    for tenth in range(100):
        store.add(DetectionsMessage("n1", camera_id, tenth / 10, 160, 90, (DetectionBox("no_helmet", 0.9, (1, 2, 30, 40), 4),)))
    packets = read_packets(base, admin, camera_id, 20)  # the first ones may still be the placeholder
    assert all(jpeg[:2] == b"\xff\xd8" for _, jpeg in packets)
    assert {"w": 160, "h": 90, "boxes": [{"l": "no_helmet", "c": 0.9, "b": [1, 2, 30, 40], "t": 4}]} in [
        {k: v for k, v in h.items() if k not in ("age", "edge")} for h, _ in packets
    ]


def test_live_needs_a_token(client):
    assert client.get("/api/cameras/1/live").status_code == 401


def read_wall_packets(base, admin, cluster_id, count, timeout=10.0):
    """The first `count` packets of the multiplexed /cameras/live, each as (header, jpeg); header carries `id`."""
    found, buf = [], b""
    deadline = time.time() + timeout
    with httpx.stream("GET", f"{base}/api/cameras/live?cluster_id={cluster_id}", headers=admin, timeout=timeout) as r:
        assert r.status_code == 200
        for chunk in r.iter_bytes():
            buf += chunk
            while len(buf) >= 8:
                head_len, jpeg_len = struct.unpack(">II", buf[:8])
                if len(buf) < 8 + head_len + jpeg_len:
                    break
                found.append((json.loads(buf[8:8 + head_len]), buf[8 + head_len:8 + head_len + jpeg_len]))
                buf = buf[8 + head_len + jpeg_len:]
            if len(found) >= count:
                return found
            assert time.time() < deadline, "no packet in time"
    return found


def test_live_wall_multiplexes_every_camera_the_grid_would_show(live, tmp_path):
    base, app = live
    admin, cam1 = make_camera(base, app, tmp_path)
    _, cam2 = make_camera(base, app, tmp_path)
    cluster_id = httpx.get(base + "/api/clusters", headers=admin).json()[0]["id"]

    packets = read_wall_packets(base, admin, cluster_id, 30)
    seen_ids = {h["id"] for h, _ in packets}
    assert {cam1, cam2} <= seen_ids
    assert all(jpeg[:2] == b"\xff\xd8" for _, jpeg in packets)


def read_wall_packets_url(base, admin, url, count, timeout=10.0):
    found, buf = [], b""
    deadline = time.time() + timeout
    with httpx.stream("GET", url, headers=admin, timeout=timeout) as r:
        assert r.status_code == 200
        for chunk in r.iter_bytes():
            buf += chunk
            while len(buf) >= 8:
                head_len, jpeg_len = struct.unpack(">II", buf[:8])
                if len(buf) < 8 + head_len + jpeg_len:
                    break
                found.append((json.loads(buf[8:8 + head_len]), buf[8 + head_len:8 + head_len + jpeg_len]))
                buf = buf[8 + head_len + jpeg_len:]
            if len(found) >= count:
                return found
            assert time.time() < deadline, "no packet in time"
    return found


def test_live_wall_pin_adds_a_camera_outside_the_grid(live, tmp_path):
    base, app = live
    admin, cam1 = make_camera(base, app, tmp_path)
    cluster_id = httpx.get(base + "/api/clusters", headers=admin).json()[0]["id"]
    other_cluster = httpx.post(base + "/api/clusters", headers=admin, json={"name": "other-cluster"}).json()
    other_node = httpx.post(base + "/api/nodes", headers=admin, json={"cluster_id": other_cluster["id"], "name": "n"}).json()
    other_cam = httpx.post(base + "/api/cameras", headers=admin, json={"node_id": other_node["id"], "name": "pinned-cam"}).json()
    folder = tmp_path / "video" / str(other_cluster["id"]) / str(other_node["id"]) / str(other_cam["id"])
    folder.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(folder / "v.avi"), cv2.VideoWriter_fourcc(*"MJPG"), 25, (160, 90))
    for i in range(250):
        writer.write(np.full((90, 160, 3), i % 255, np.uint8))
    writer.release()

    without_pin = read_wall_packets(base, admin, cluster_id, 5)
    assert other_cam["id"] not in {h["id"] for h, _ in without_pin}  # not pinned: the other cluster's camera is absent

    with_pin = read_wall_packets_url(base, admin, f"{base}/api/cameras/live?cluster_id={cluster_id}&pin={other_cam['id']}", 10)
    assert other_cam["id"] in {h["id"] for h, _ in with_pin}


def test_live_wall_needs_a_token(client):
    assert client.get("/api/cameras/live").status_code == 401


def test_live_wall_with_an_empty_cluster_is_an_empty_but_open_stream(live, tmp_path):
    base, app = live
    admin, _ = make_camera(base, app, tmp_path)
    cluster = httpx.post(base + "/api/clusters", headers=admin, json={"name": "empty-wall"}).json()
    with httpx.stream("GET", f"{base}/api/cameras/live?cluster_id={cluster['id']}", headers=admin, timeout=5) as r:
        assert r.status_code == 200  # the connection itself opens fine; with no camera, nothing is ever sent on it

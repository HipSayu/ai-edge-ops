"""One process may run several nodes (a mock fleet sharing one model); each is its own node on the broker."""

import json

import pytest

from edge.bootstrap.settings import Settings


def test_a_single_node_is_the_classic_settings():
    s = Settings(node_id="edge-b1", cameras=[{"id": 1, "uri": "file:///v.mp4"}], mqtt_password="pw")
    [node] = s.node_configs()
    assert (node.node_id, node.mqtt_password, [c.id for c in node.cameras]) == ("edge-b1", "pw", [1])


def test_several_nodes_each_carry_their_own_password_and_cameras(monkeypatch):
    monkeypatch.setenv("EDGE_NODES", json.dumps([
        {"node_id": "edge-c1", "mqtt_password": "a", "cameras": [{"id": 53, "uri": "rtsp://c/53"}]},
        {"node_id": "edge-d1", "mqtt_password": "b", "cameras": [{"id": 61, "uri": "rtsp://c/61"}, {"id": 62, "uri": "rtsp://c/62"}]},
    ]))
    nodes = Settings().node_configs()
    assert [(n.node_id, n.mqtt_password, len(n.cameras)) for n in nodes] == [("edge-c1", "a", 1), ("edge-d1", "b", 2)]


def test_without_any_node_it_says_what_to_set(monkeypatch):
    monkeypatch.delenv("EDGE_NODE_ID", raising=False)
    with pytest.raises(ValueError, match="EDGE_NODES"):
        Settings(_env_file=None).node_configs()

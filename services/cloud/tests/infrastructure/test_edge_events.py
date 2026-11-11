"""Edge events are filed like local detections."""

from edge_link import ViolationMessage

from cloud.bootstrap.edge_events import build_edge_events
from cloud.bootstrap.settings import Settings


def event(**changes):
    fields = dict(event_id="e1", node_id="n1", camera_id=3, violation_type="no_helmet", confidence=0.9,
                  occurred_at="2026-10-21T01:00:00+00:00", video_ts_sec=4.5, snapshot_jpeg=b"jpeg")
    fields.update(changes)
    return ViolationMessage(**fields)


def subscriber(filed):
    return build_edge_events(Settings(mqtt_host="broker"), lambda *args: filed.append(args))


def test_no_broker_means_no_subscriber():
    assert build_edge_events(Settings(), lambda *args: None) is None


def test_event_is_filed_with_the_recorders_arguments():
    filed = []
    assert subscriber(filed).handle(event().to_json())
    assert filed == [(3, "no_helmet", 0.9, 4.5, b"jpeg")]


def test_unknown_violation_type_is_not_filed():
    filed = []
    subscriber(filed).handle(event(violation_type="no_hat").to_json())
    assert filed == []


def test_redelivered_event_is_filed_once():
    filed = []
    sub = subscriber(filed)
    sub.handle(event().to_json())
    sub.handle(event().to_json())
    assert len(filed) == 1

"""Messages, topics, and the two ends of the link (with a fake MQTT client in place of the broker)."""

import json

import pytest

from edge_link import DetectionBox, DetectionsMessage, EventPublisher, EventSubscriber, MemorySeen, ViolationMessage
from edge_link.topics import DETECTIONS_FILTER, EVENTS_FILTER, detections_topic, events_topic, status_topic


def message(**changes) -> ViolationMessage:
    fields = dict(event_id="e1", node_id="n1", camera_id=3, violation_type="no_helmet", confidence=0.91234567,
                  occurred_at="2026-10-21T01:00:00+00:00", video_ts_sec=4.56789, snapshot_jpeg=b"\xff\xd8jpeg")
    fields.update(changes)
    return ViolationMessage(**fields)


class FakeInfo:
    def __init__(self, acknowledged: bool) -> None:
        self.acknowledged = acknowledged

    def wait_for_publish(self, timeout=None):
        pass

    def is_published(self) -> bool:
        return self.acknowledged


class FakeClient:
    def __init__(self, client_id: str) -> None:
        self.client_id, self.published, self.subscribed = client_id, [], []
        self.will = self.credentials = self.address = self.tls_ca = None
        self.on_connect = self.on_message = None
        self.started = False
        self.connected, self.acknowledges = True, True  # what the broker is doing, for deliver()

    def is_connected(self) -> bool:
        return self.connected

    def username_pw_set(self, user, password):
        self.credentials = (user, password)

    def tls_set(self, ca_certs=None, **kwargs):
        self.tls_ca = ca_certs

    def will_set(self, topic, payload, qos, retain):
        self.will = (topic, payload, qos, retain)

    def connect_async(self, host, port):
        self.address = (host, port)

    def loop_start(self):
        self.started = True

    def loop_stop(self):
        self.started = False

    def disconnect(self):
        pass

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, payload, qos, retain))
        return FakeInfo(self.acknowledges)

    def subscribe(self, topic, qos=0):
        self.subscribed.append((topic, qos))


def publisher(**kwargs):
    clients = []

    def factory(client_id):
        clients.append(FakeClient(client_id))
        return clients[0]

    return EventPublisher("n1", "broker", 1884, client_factory=factory, **kwargs), clients[0]


def subscriber(handler=None, **kwargs):
    handled = []
    clients = []

    def factory(client_id):
        clients.append(FakeClient(client_id))
        return clients[0]

    sub = EventSubscriber("broker", 1883, handler or handled.append, client_factory=factory, **kwargs)
    return sub, handled, clients[0]


# ---------------------------------------------------------------- topics and messages

def test_topics():
    assert events_topic("n1", 3) == "ppe/n1/cameras/3/events"
    assert status_topic("n1") == "ppe/n1/status"
    assert EVENTS_FILTER == "ppe/+/cameras/+/events"


def test_round_trip_keeps_the_event_and_rounds_numbers():
    assert ViolationMessage.parse(message().to_json()) == message(confidence=0.9123, video_ts_sec=4.568)


def test_wire_format_keys():
    assert set(json.loads(message().to_json())) == {
        "event_id", "node_id", "camera_id", "violation_type", "confidence", "occurred_at", "video_ts_sec",
        "snapshot_jpeg_b64",
    }


def test_video_ts_is_optional_on_the_way_in():
    body = json.loads(message().to_json())
    del body["video_ts_sec"]
    assert ViolationMessage.parse(json.dumps(body)).video_ts_sec == 0.0


@pytest.mark.parametrize("payload", ["not json", "{}", "[]", "null", '{"event_id": 1}'])
def test_malformed_payloads_raise_value_error(payload):
    with pytest.raises(ValueError):
        ViolationMessage.parse(payload)


@pytest.mark.parametrize("changes", [{"camera_id": "x"}, {"snapshot_jpeg_b64": "***"}])
def test_bad_field_values_raise_value_error(changes):
    body = json.loads(message().to_json())
    body.update(changes)
    with pytest.raises(ValueError):
        ViolationMessage.parse(json.dumps(body))


# ---------------------------------------------------------------- the edge end

def test_publisher_sends_the_event_on_its_topic_with_qos_1():
    pub, client = publisher()
    pub.send(message())
    topic, payload, qos, retain = client.published[0]
    assert (topic, qos, retain) == ("ppe/n1/cameras/3/events", 1, False)
    assert ViolationMessage.parse(payload).event_id == "e1"


def test_publisher_status_is_online_on_connect_and_offline_as_last_will():
    pub, client = publisher(username="u", password="p")
    assert client.will == (status_topic("n1"), "offline", 1, True)
    assert client.credentials == ("u", "p")
    pub.start()
    assert client.address == ("broker", 1884) and client.started
    client.on_connect(client, None, None, 0)
    assert client.published[-1] == (status_topic("n1"), "online", 1, True)
    pub.stop()
    assert client.published[-1] == (status_topic("n1"), "offline", 1, True)
    assert not client.started


# ---------------------------------------------------------------- the cloud end

def test_subscriber_subscribes_on_every_connect():
    sub, _, client = subscriber()
    sub.start()
    assert client.address == ("broker", 1883) and client.started
    client.on_connect(client, None, None, 0)
    client.on_connect(client, None, None, 0)
    assert client.subscribed == [(EVENTS_FILTER, 1)] * 2


def test_what_the_publisher_sends_the_subscriber_receives_once():
    pub, pub_client = publisher()
    sub, handled, sub_client = subscriber()
    pub.send(message())

    class Delivered:
        payload = pub_client.published[0][1].encode()

    sub_client.on_message(sub_client, None, Delivered())
    sub_client.on_message(sub_client, None, Delivered())  # QoS 1 redelivery
    assert [m.event_id for m in handled] == ["e1"]


def test_malformed_messages_are_dropped_without_raising():
    sub, handled, _ = subscriber()
    for bad in ("not json", "{}", '{"event_id": "x"}'):
        assert not sub.handle(bad)
    assert handled == []


def test_a_failing_handler_does_not_stop_the_subscriber_and_the_event_can_come_again():
    calls = []

    def handler(event):
        calls.append(event)
        if len(calls) == 1:
            raise RuntimeError("unknown camera")

    sub, _, _ = subscriber(handler)
    assert not sub.handle(message().to_json())
    assert sub.handle(message().to_json())


def test_tls_is_set_up_only_when_a_ca_is_given():
    assert publisher()[1].tls_ca is None and subscriber()[2].tls_ca is None
    assert publisher(tls_ca="ca.pem")[1].tls_ca == "ca.pem"
    assert subscriber(tls_ca="ca.pem")[2].tls_ca == "ca.pem"


class SharedSeen:
    """Stands in for a store two subscribers (two cloud instances) share."""

    def __init__(self):
        self.ids = set()

    def claim(self, event_id):
        if event_id in self.ids:
            return False
        self.ids.add(event_id)
        return True

    def release(self, event_id):
        self.ids.discard(event_id)


def test_subscribers_sharing_a_seen_store_take_an_event_once_between_them():
    shared = SharedSeen()
    first, handled_a, _ = subscriber(seen=shared)
    second, handled_b, _ = subscriber(seen=shared)
    assert first.handle(message().to_json()) and not second.handle(message().to_json())
    assert len(handled_a) + len(handled_b) == 1


def test_memory_seen_forgets_the_oldest_beyond_its_limit():
    seen = MemorySeen(remembered=2)
    assert [seen.claim(i) for i in "abc"] == [True, True, True]
    assert seen.claim("a")  # "a" was pushed out by "c"
    assert not seen.claim("c")
    seen.release("c")
    assert seen.claim("c")


def test_detections_round_trip_and_keep_the_boxes():
    box = DetectionBox("no_helmet", 0.91234, (1, 2, 30, 40), 7)
    original = DetectionsMessage("n1", 3, 12.3456, 1280, 720, (box, DetectionBox("person", 0.5, (5, 6, 7, 8))))
    back = DetectionsMessage.parse(original.to_json())
    assert (back.node_id, back.camera_id, back.video_ts_sec, back.width, back.height) == ("n1", 3, 12.346, 1280, 720)
    assert back.boxes == (DetectionBox("no_helmet", 0.912, (1, 2, 30, 40), 7), DetectionBox("person", 0.5, (5, 6, 7, 8), None))


@pytest.mark.parametrize("payload", ["not json", "{}", '{"node_id": "n", "camera_id": 1, "ts": 0, "w": 1, "h": 1, "boxes": [[1]]}'])
def test_malformed_detections_raise_value_error(payload):
    with pytest.raises(ValueError):
        DetectionsMessage.parse(payload)


def test_the_publisher_sends_boxes_on_their_topic_with_qos_0():
    pub, client = publisher()
    pub.send_detections(DetectionsMessage("n1", 3, 1.0, 640, 360, ()))
    topic, _, qos, _ = client.published[0]
    assert (topic, qos) == (detections_topic("n1", 3), 0)


def test_the_subscriber_listens_to_boxes_only_when_asked_and_tells_them_from_events():
    boxes = []
    sub, handled, client = subscriber(on_detections=boxes.append)
    client.on_connect(client, None, None, 0)
    assert (DETECTIONS_FILTER, 0) in client.subscribed and (EVENTS_FILTER, 1) in client.subscribed

    class Delivered:
        topic = detections_topic("n1", 3)
        payload = DetectionsMessage("n1", 3, 1.0, 640, 360, ()).to_json().encode()

    client.on_message(client, None, Delivered())
    assert len(boxes) == 1 and handled == []  # not mistaken for an event

    deaf, _, deaf_client = subscriber()
    deaf_client.on_connect(deaf_client, None, None, 0)
    assert all(topic != DETECTIONS_FILTER for topic, _ in deaf_client.subscribed)


def test_deliver_reports_the_brokers_acknowledgement():
    pub, client = publisher()
    assert pub.deliver(message()) is True
    assert client.published[-1][0] == events_topic("n1", 3) and client.published[-1][2] == 1
    client.acknowledges = False
    assert pub.deliver(message()) is False


def test_deliver_hands_nothing_to_the_client_while_the_link_is_down():
    pub, client = publisher()
    client.connected = False
    assert pub.deliver(message()) is False
    assert client.published == []  # the caller keeps the event; the client does not queue a second copy


# ---------------------------------------------------------------- zones (cloud to edge)

from edge_link import ZoneSpec, ZonesMessage, ZonesPublisher, ZonesSubscriber  # noqa: E402
from edge_link.topics import zones_topic  # noqa: E402

SQUARE = ((0.1, 0.1), (0.5, 0.1), (0.5, 0.5), (0.1, 0.5))


def zones_message(camera_id=3) -> ZonesMessage:
    return ZonesMessage(camera_id, (ZoneSpec(7, "Cẩu tháp", SQUARE), ZoneSpec(8, "Hố móng", SQUARE, enabled=False)))


def _client_of(factory_list):
    def factory(client_id):
        factory_list.append(FakeClient(client_id))
        return factory_list[0]

    return factory


def zones_publisher():
    clients = []
    return ZonesPublisher("broker", 8883, "cloud", "pw", client_factory=_client_of(clients)), clients


def zones_subscriber(camera_ids, handled):
    clients = []
    return ZonesSubscriber(camera_ids, "broker", 8883, handled.append, client_factory=_client_of(clients)), clients


def test_zones_topic_is_per_camera_and_independent_of_the_node():
    assert zones_topic(3) == "ppe/config/cameras/3/zones"


def test_zones_message_round_trip():
    assert ZonesMessage.parse(zones_message().to_json()) == zones_message()
    assert ZonesMessage.parse(ZonesMessage(3, ()).to_json()).zones == ()


@pytest.mark.parametrize("zone", [
    {"id": 1, "name": "a", "polygon": [[0, 0], [1, 1]]},                      # two corners
    {"id": 1, "name": "a", "polygon": [[0, 0], [1, 0], [2, 1]]},              # outside the frame
    {"id": 1, "polygon": [[0, 0], [1, 0], [1, 1]]},                           # no name
    {"id": "x", "name": "a", "polygon": [[0, 0], [1, 0], [1, 1]]},            # bad id
])
def test_bad_zones_raise_value_error(zone):
    with pytest.raises(ValueError):
        ZonesMessage.parse(json.dumps({"camera_id": 3, "zones": [zone]}))


def test_zones_are_published_retained_with_qos_1_on_the_camera_topic():
    pub, clients = zones_publisher()
    pub.start()
    client = clients[0]
    assert client.credentials == ("cloud", "pw") and client.started
    assert pub.publish(zones_message()) is True
    topic, payload, qos, retain = client.published[0]
    assert (topic, qos, retain) == ("ppe/config/cameras/3/zones", 1, True)
    assert ZonesMessage.parse(payload) == zones_message()


def test_the_edge_subscribes_to_the_zones_of_its_own_cameras_after_every_connect():
    sub, clients = zones_subscriber([5, 3], [])
    client = clients[0]
    client.on_connect(client, None, None, 0)
    client.on_connect(client, None, None, 0)  # a reconnect subscribes again
    assert client.subscribed == [(zones_topic(3), 1), (zones_topic(5), 1)] * 2


def test_the_edge_applies_zones_of_its_cameras_and_ignores_the_rest():
    handled = []
    sub, _ = zones_subscriber([3], handled)
    assert sub.handle(zones_message(3).to_json()) is True
    assert sub.handle(zones_message(4).to_json()) is False   # a camera of another node
    assert sub.handle("not json") is False
    assert [m.camera_id for m in handled] == [3]


def test_a_failing_handler_does_not_stop_the_edge_listening():
    def boom(message):
        raise RuntimeError("disk full")

    clients = []
    sub = ZonesSubscriber([3], "b", 1, boom, client_factory=_client_of(clients))
    assert sub.handle(zones_message(3).to_json()) is False

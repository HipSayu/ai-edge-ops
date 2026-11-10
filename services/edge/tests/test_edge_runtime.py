"""The camera logic with fakes, the runtime over a fake stream, the MQTT message contract and the renderer."""

import cv2
import numpy as np
from support import Frame, Pipe

from edge_link import ViolationMessage
from edge_link.topics import events_topic
from edge.application.camera_logic import CameraLogic
from edge.application.runtime import EdgeRuntime, NodeStream
from edge.domain.cooldown import Cooldown
from edge.domain.detection import Detection
from edge.infrastructure.jpeg_renderer import JpegRenderer
from edge.infrastructure.mqtt_publisher import MqttEventPublisher

CLASSES = frozenset({"no_helmet", "no_vest"})


class FakeDetector:
    def __init__(self, *labels: str) -> None:
        self.labels, self.calls = labels, 0

    def detect(self, image):
        self.calls += 1
        return [Detection(label, 0.9, (1, 1, 20, 20)) for label in self.labels]


class FakeRenderer:
    def __init__(self) -> None:
        self.calls = 0

    def render(self, image, detections):
        self.calls += 1
        return b"jpeg"


class Sink:
    def __init__(self) -> None:
        self.events = []

    def publish(self, event) -> None:
        self.events.append(event)


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def frame(ts=0.0):
    return Frame(np.zeros((40, 40, 3), np.uint8), ts)


def pipeline(detector, sink, renderer=None, cooldown=5.0, clock=None):
    logic = CameraLogic(
        node_id="n1", camera_id=7, renderer=renderer or FakeRenderer(), publisher=sink,
        violation_classes=CLASSES, cooldown=Cooldown(cooldown), clock=clock or Clock(),
    )
    return Pipe(logic, detector)


# ---------------------------------------------------------------- pipeline

def test_violation_becomes_an_event_with_its_snapshot():
    sink = Sink()
    assert pipeline(FakeDetector("no_helmet"), sink).process(frame(12.5)) == 1
    event = sink.events[0]
    assert (event.node_id, event.camera_id, event.violation_type) == ("n1", 7, "no_helmet")
    assert event.video_ts_sec == 12.5 and event.snapshot_jpeg == b"jpeg" and event.event_id


def test_other_classes_are_not_violations():
    sink = Sink()
    assert pipeline(FakeDetector("person", "helmet"), sink).process(frame()) == 0
    assert sink.events == []


def test_one_snapshot_is_shared_by_the_events_of_a_frame():
    sink, renderer = Sink(), FakeRenderer()
    pipeline(FakeDetector("no_helmet", "no_vest"), sink, renderer).process(frame())
    assert len(sink.events) == 2 and renderer.calls == 1


def test_cooldown_holds_back_repeats_of_the_same_violation():
    sink, clock = Sink(), Clock()
    p = pipeline(FakeDetector("no_helmet"), sink, clock=clock)
    p.process(frame())
    clock.now = 2.0
    p.process(frame())
    assert len(sink.events) == 1
    clock.now = 6.0
    p.process(frame())
    assert len(sink.events) == 2


def test_cooldown_is_per_violation_type():
    sink = Sink()
    p = pipeline(FakeDetector("no_helmet"), sink)
    p.process(frame())
    p.detector = FakeDetector("no_vest")
    p.process(frame())
    assert [e.violation_type for e in sink.events] == ["no_helmet", "no_vest"]


def seen(label="no_helmet"):
    return [Detection(label, 0.9, (1, 1, 5, 5))]


class FakeStream:
    """Stands in for DeepStream: hands the handler what it is told to, once, then returns (or raises)."""

    def __init__(self, items, fail: Exception | None = None) -> None:
        self.items, self.fail = items, fail

    def run(self, handler, stop) -> None:
        for camera_id, detections in self.items:
            handler(camera_id, 1.0, 40, 40, detections, lambda: np.zeros((40, 40, 3), np.uint8))
        if self.fail:
            raise self.fail


def logic_of(camera_id: int, sink, cls=CameraLogic) -> CameraLogic:
    return cls(node_id="n1", camera_id=camera_id, renderer=FakeRenderer(), publisher=sink,
               violation_classes=CLASSES, cooldown=Cooldown(5.0), clock=Clock())


def run_to_end(*nodes: NodeStream) -> None:
    runtime = EdgeRuntime(list(nodes))
    runtime.start()
    runtime.wait()


def test_the_runtime_gives_each_camera_its_own_detections():
    sink = Sink()
    stream = FakeStream([(1, seen("no_helmet")), (2, seen("no_vest"))])
    run_to_end(NodeStream("n1", stream, {1: logic_of(1, sink), 2: logic_of(2, sink)}))
    assert sorted((e.camera_id, e.violation_type) for e in sink.events) == [(1, "no_helmet"), (2, "no_vest")]


def test_a_camera_that_breaks_does_not_stop_the_others_in_the_stream():
    class Broken(CameraLogic):
        def handle(self, *args, **kwargs):
            raise RuntimeError("logic broke")

    sink = Sink()
    stream = FakeStream([(1, seen()), (2, seen())])
    run_to_end(NodeStream("n1", stream, {1: logic_of(1, sink, Broken), 2: logic_of(2, sink)}))
    assert [e.camera_id for e in sink.events] == [2]


def test_a_node_whose_stream_fails_does_not_stop_the_other_node():
    sink = Sink()
    bad = NodeStream("bad", FakeStream([], fail=RuntimeError("no GPU")), {})
    good = NodeStream("good", FakeStream([(1, seen())]), {1: logic_of(1, sink)})
    run_to_end(bad, good)
    assert len(sink.events) == 1


def test_a_detection_for_an_unknown_camera_is_ignored():
    sink = Sink()
    run_to_end(NodeStream("n1", FakeStream([(99, seen())]), {1: logic_of(1, sink)}))
    assert sink.events == []


def test_the_picture_is_fetched_only_when_an_event_needs_it():
    fetched = []

    def picture():
        fetched.append(1)
        return np.zeros((40, 40, 3), np.uint8)

    logic = logic_of(1, Sink())
    logic.handle(1.0, 40, 40, seen("person"), picture)
    assert fetched == []
    logic.handle(2.0, 40, 40, seen("no_helmet"), picture)
    assert fetched == [1]


# ---------------------------------------------------------------- MQTT adapter

class FakeClient:
    def __init__(self, client_id: str) -> None:
        self.published = []

    def will_set(self, *args, **kwargs):
        pass

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, payload, qos))


def test_adapter_sends_the_event_as_the_shared_message():
    sink = Sink()
    pipeline(FakeDetector("no_helmet"), sink).process(frame(3.0))
    event = sink.events[0]
    clients = []
    adapter = MqttEventPublisher("n1", "broker", client_factory=lambda cid: clients.append(FakeClient(cid)) or clients[0])
    adapter.publish(event)

    topic, payload, qos = clients[0].published[0]
    assert topic == events_topic("n1", 7) and qos == 1
    message = ViolationMessage.parse(payload)
    assert (message.event_id, message.camera_id, message.violation_type) == (event.event_id, 7, "no_helmet")
    assert message.video_ts_sec == 3.0 and message.snapshot_jpeg == b"jpeg"
    assert message.occurred_at == event.occurred_at.isoformat()


# ---------------------------------------------------------------- renderer

def test_renderer_makes_a_small_jpeg():
    image = np.zeros((1080, 1920, 3), np.uint8)
    data = JpegRenderer(max_width=960).render(image, [Detection("no_helmet", 0.8, (100, 100, 300, 400))])
    assert data[:2] == b"\xff\xd8"
    decoded = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    assert decoded.shape[1] == 960


class BoxSink:
    def __init__(self):
        self.sent = []

    def publish_detections(self, camera_id, ts_sec, width, height, detections, fps=0.0, infer_ms=0.0, dropped=0):
        self.sent.append((camera_id, ts_sec, width, height, [d.label for d in detections]))


def test_every_box_goes_to_the_sink_not_only_the_violations():
    sink = BoxSink()
    p = pipeline(FakeDetector("person", "no_helmet"), Sink())
    p.detection_sink = sink
    p.process(frame(4.5))
    assert sink.sent == [(7, 4.5, 40, 40, ["person", "no_helmet"])]  # (camera, position, width, height, labels)


def test_the_adapter_sends_the_boxes_over_the_link():
    mqtt = MqttEventPublisher("n1", "broker", client_factory=lambda cid: FakeClient(cid))
    client = mqtt._link._client
    mqtt.publish_detections(7, 2.0, 640, 360, [Detection("no_helmet", 0.9, (1, 2, 3, 4), 5)])
    topic, payload, qos = client.published[0]
    assert topic == "ppe/n1/cameras/7/detections" and qos == 0
    assert '"no_helmet"' in payload and '"ts":2.0' in payload

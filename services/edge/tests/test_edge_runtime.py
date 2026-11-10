"""The pipeline with fakes, the MQTT message contract, the video source and the renderer."""

import threading
import time
from pathlib import Path

import cv2
import numpy as np

from edge_link import ViolationMessage
from edge_link.topics import events_topic
from edge.application.latest_frame import LatestFrame
from edge.application.pipeline import CameraPipeline
from edge.application.ports import Frame
from edge.application.runtime import EdgeRuntime
from edge.domain.cooldown import Cooldown
from edge.domain.detection import Detection
from edge.infrastructure.jpeg_renderer import JpegRenderer
from edge.infrastructure.mqtt_publisher import MqttEventPublisher
from edge.infrastructure.video_source import VideoFileSource

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


def pipeline(detector, sink, renderer=None, every_n=1, cooldown=5.0, clock=None, source=None):
    return CameraPipeline(
        node_id="n1", camera_id=7, source=source, detector=detector, renderer=renderer or FakeRenderer(), publisher=sink,
        violation_classes=CLASSES, every_n=every_n, cooldown=Cooldown(cooldown), clock=clock or Clock(),
    )


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


class MarkedDetector:
    """Remembers which frame it was shown (the frames are filled with their number), and takes `pause` seconds."""

    def __init__(self, pause: float = 0.0, fail_on: int | None = None) -> None:
        self.seen, self.pause, self.fail_on = [], pause, fail_on

    def detect(self, image):
        mark = int(image[0, 0, 0])
        self.seen.append(mark)
        time.sleep(self.pause)
        if mark == self.fail_on:
            raise RuntimeError("model crashed")
        return []


def marked(n: int) -> Frame:
    return Frame(np.full((4, 4, 3), n, np.uint8), float(n))


class Frames:
    """A source of numbered frames, `gap` seconds apart."""

    def __init__(self, count: int, gap: float = 0.0) -> None:
        self.count, self.gap = count, gap

    def frames(self):
        for n in range(self.count):
            yield marked(n)
            time.sleep(self.gap)


def test_the_latest_frame_slot_hands_out_only_the_newest():
    slot = LatestFrame()
    for n in range(3):
        slot.put(marked(n))
    index, newest = slot.take(0)
    assert (index, newest.ts_sec) == (2, 2.0)


def test_taking_waits_for_a_frame_that_is_new_enough():
    slot = LatestFrame()
    slot.put(marked(0))
    threading.Timer(0.1, lambda: slot.put(marked(1))).start()
    assert slot.take(1, timeout=2)[0] == 1
    assert slot.take(5, timeout=0.05) is None  # nothing that new came
    slot.close()
    assert slot.take(5, timeout=2) is None and slot.closed  # and nothing will


def test_a_slow_detector_drops_frames_and_ends_on_the_newest():
    detector = MarkedDetector(pause=0.05)  # about ten times slower than the camera below
    p = pipeline(detector, Sink(), every_n=1, source=Frames(40, gap=0.005))
    p.run(threading.Event())
    assert 2 < len(detector.seen) < 15  # it did not work through all 40
    assert detector.seen[-1] == 39  # and what it saw last is what the camera showed last
    assert p.dropped == 40 - len(detector.seen)


def test_the_detector_looks_at_most_once_per_every_n_frames():
    detector = MarkedDetector()
    pipeline(detector, Sink(), every_n=4, source=Frames(24, gap=0.01)).run(threading.Event())
    gaps = [b - a for a, b in zip(detector.seen, detector.seen[1:])]
    assert gaps and min(gaps) >= 4
    assert len(detector.seen) >= 3


def test_a_failing_detector_stops_the_camera_with_its_error():
    p = pipeline(MarkedDetector(fail_on=0), Sink(), every_n=1, source=Frames(200, gap=0.005))
    try:
        p.run(threading.Event())
    except RuntimeError as error:
        assert "model crashed" in str(error)
    else:
        raise AssertionError("the error was swallowed")


# ---------------------------------------------------------------- runtime

class OneFrameSource:
    def frames(self):
        yield frame()


class BrokenSource:
    def frames(self):
        raise RuntimeError("camera unplugged")
        yield  # pragma: no cover


def test_a_broken_camera_does_not_stop_the_others():
    sink = Sink()
    good = pipeline(FakeDetector("no_helmet"), sink, source=OneFrameSource())
    bad = pipeline(FakeDetector(), sink, source=BrokenSource())
    runtime = EdgeRuntime([bad, good])
    runtime.start()
    runtime.wait()
    assert len(sink.events) == 1


def test_stop_ends_a_running_camera():
    class Endless:
        def frames(self):
            while True:
                yield frame()

    runtime = EdgeRuntime([pipeline(FakeDetector(), Sink(), source=Endless())])
    runtime.start()
    runtime.stop()
    assert not any(t.is_alive() for t in runtime._threads)


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


# ---------------------------------------------------------------- video source and renderer

def write_video(path: Path, frames: int = 5) -> None:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 100.0, (64, 48))
    for i in range(frames):
        writer.write(np.full((48, 64, 3), i * 20, np.uint8))
    writer.release()


def test_video_source_plays_files_in_name_order_without_looping(tmp_path):
    write_video(tmp_path / "a.avi", 3)
    write_video(tmp_path / "b.avi", 2)
    frames = list(VideoFileSource(tmp_path, loop=False).frames())
    assert len(frames) == 5
    assert [f.ts_sec for f in frames][:3] == sorted(f.ts_sec for f in frames[:3])


def test_video_source_loops_until_stopped(tmp_path):
    write_video(tmp_path / "a.avi", 3)
    source = VideoFileSource(tmp_path / "a.avi", loop=True).frames()
    assert len([next(source) for _ in range(7)]) == 7


def test_video_source_without_a_video_fails_loudly(tmp_path):
    try:
        next(VideoFileSource(tmp_path / "nothing").frames())
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")


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

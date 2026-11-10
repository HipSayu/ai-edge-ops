"""Confirmation, per-person cooldown, the ByteTrack adapter, the outbox and the sender that drains it."""

import threading
import time

import numpy as np

from edge.application.durable_publisher import DurablePublisher
from edge.application.pipeline import CameraPipeline
from edge.application.ports import Frame
from edge.domain.confirmation import Confirmation
from edge.domain.cooldown import Cooldown
from edge.domain.detection import Detection
from edge.domain.event import ViolationEvent
from edge.infrastructure.bytetrack_tracker import ByteTrackTracker
from edge.infrastructure.sqlite_outbox import SqliteOutbox

CLASSES = frozenset({"no_helmet", "no_vest"})


def frame():
    return Frame(np.zeros((40, 40, 3), np.uint8), 0.0)


class Scripted:
    """Returns the next list of detections each time it is asked."""

    def __init__(self, *rounds) -> None:
        self.rounds = list(rounds)

    def detect(self, image):
        return self.rounds.pop(0)


class Ids:
    """A tracker that numbers the detections by their position."""

    def update(self, detections):
        return [Detection(d.label, d.confidence, d.box, i + 1) for i, d in enumerate(detections)]


class Sink:
    def __init__(self) -> None:
        self.events = []

    def publish(self, event) -> None:
        self.events.append(event)


class Renderer:
    def render(self, image, detections):
        return b"jpeg"


def pipeline(detector, sink, **kwargs):
    return CameraPipeline(
        node_id="n1", camera_id=1, source=None, detector=detector, renderer=Renderer(), publisher=sink,
        violation_classes=CLASSES, every_n=1, cooldown=Cooldown(5.0), clock=lambda: 0.0, **kwargs,
    )


def det(label="no_helmet", box=(10, 10, 30, 30), conf=0.9):
    return Detection(label, conf, box)


# ---------------------------------------------------------------- confirmation

def test_a_violation_is_confirmed_after_min_frames_sightings():
    c = Confirmation(min_frames=3)
    assert [c.confirm("a", t) for t in (0.0, 0.1, 0.2)] == [False, False, True]


def test_keys_are_counted_apart():
    c = Confirmation(min_frames=2)
    assert not c.confirm("a", 0.0) and not c.confirm("b", 0.0)
    assert c.confirm("a", 0.1)


def test_a_key_not_seen_for_a_while_starts_over():
    c = Confirmation(min_frames=2, forget_after=5.0)
    c.confirm("a", 0.0)
    assert not c.confirm("a", 10.0)  # the first sighting was forgotten
    assert c.confirm("a", 10.5)


def test_a_one_frame_false_alarm_sends_nothing():
    sink = Sink()
    p = pipeline(Scripted([det()], [], [det()]), sink, confirmation=Confirmation(min_frames=2, forget_after=60.0))
    for _ in range(3):
        p.process(frame())
    assert len(sink.events) == 1  # the 2nd sighting confirmed it; the empty frame between did not reset it


def test_not_confirmed_means_nothing_sent():
    sink = Sink()
    pipeline(Scripted([det()]), sink, confirmation=Confirmation(min_frames=2)).process(frame())
    assert sink.events == []


# ---------------------------------------------------------------- per person

def test_two_people_without_helmets_are_two_events():
    sink = Sink()
    pipeline(Scripted([det(box=(1, 1, 9, 9)), det(box=(20, 20, 39, 39))]), sink, tracker=Ids()).process(frame())
    assert len(sink.events) == 2


def test_without_a_tracker_they_share_one_cooldown():
    sink = Sink()
    pipeline(Scripted([det(box=(1, 1, 9, 9)), det(box=(20, 20, 39, 39))]), sink).process(frame())
    assert len(sink.events) == 1


def test_cooldown_old_keys_are_forgotten():
    c = Cooldown(5.0)
    for i in range(100):
        c.allow(f"{i}:no_helmet", float(i) * 10)
    assert len(c._last) == 1


# ---------------------------------------------------------------- ByteTrack

def test_bytetrack_keeps_the_id_of_a_moving_person():
    tracker = ByteTrackTracker()
    ids = []
    for step in range(5):
        out = tracker.update([det(box=(100 + 3 * step, 100, 160 + 3 * step, 260))])
        ids.append(out[0].track_id)
    assert ids[-1] is not None and len(set(ids[1:])) == 1


def test_bytetrack_gives_two_people_two_ids():
    tracker = ByteTrackTracker()
    for _ in range(3):
        out = tracker.update([det(box=(10, 10, 60, 160)), det(box=(300, 10, 350, 160))])
    assert out[0].track_id is not None and out[1].track_id is not None and out[0].track_id != out[1].track_id


def test_bytetrack_survives_an_empty_frame():
    tracker = ByteTrackTracker()
    for _ in range(3):
        before = tracker.update([det(box=(10, 10, 60, 160))])[0].track_id
    assert tracker.update([]) == []
    assert tracker.update([det(box=(10, 10, 60, 160))])[0].track_id == before


def test_each_camera_numbers_its_tracks_from_one():
    a, b = ByteTrackTracker(), ByteTrackTracker()
    for _ in range(3):
        a.update([det(box=(10, 10, 60, 160))])
    assert b.update([det(box=(300, 10, 350, 160))])[0].track_id == 1


def test_a_new_label_does_not_disturb_the_ids_of_the_others():
    tracker = ByteTrackTracker()
    first = tracker.update([det("no_helmet", (10, 10, 60, 160))])[0].track_id
    tracker.update([det("no_helmet", (10, 10, 60, 160)), det("no_vest", (300, 10, 350, 160))])
    out = tracker.update([det("no_helmet", (10, 10, 60, 160)), det("no_vest", (300, 10, 350, 160)),
                          det("no_helmet", (200, 10, 250, 160))])
    assert out[0].track_id == first and len({d.track_id for d in out}) == 3


def test_labels_are_followed_apart():
    tracker = ByteTrackTracker()
    for _ in range(3):
        out = tracker.update([det("no_helmet", (10, 10, 60, 160)), det("no_vest", (12, 12, 62, 162))])
    assert out[0].track_id != out[1].track_id and None not in (out[0].track_id, out[1].track_id)


# ---------------------------------------------------------------- outbox and its sender

def event(i=0):
    return ViolationEvent("n1", 1, "no_helmet", 0.9, float(i), b"")


class Broker:
    """A target that acknowledges events, or refuses them while `up` is False."""

    def __init__(self, up: bool = True) -> None:
        self.up, self.events = up, []

    def deliver(self, e) -> bool:
        if self.up:
            self.events.append(e)
        return self.up


def durable(target, max_events=500):
    outbox = SqliteOutbox(":memory:", max_events)
    return DurablePublisher(outbox, target, retry_min=0.01, retry_max=0.02), outbox


def wait_until(condition, timeout=3.0):
    deadline = time.monotonic() + timeout
    while not condition() and time.monotonic() < deadline:
        time.sleep(0.01)
    return condition()


def test_publish_does_not_wait_for_the_target():
    gate = threading.Event()

    class Slow:
        def deliver(self, e):
            gate.wait(2)
            return True

    sender, _ = durable(Slow())
    sender.start()
    started = time.monotonic()
    for i in range(5):
        sender.publish(event(i))
    assert time.monotonic() - started < 0.5
    gate.set()
    sender.stop()


def test_events_are_sent_in_order_and_leave_the_outbox_once_acknowledged():
    broker = Broker()
    sender, outbox = durable(broker)
    sender.start()
    for i in range(20):
        sender.publish(event(i))
    sender.stop()
    assert [e.video_ts_sec for e in broker.events] == [float(i) for i in range(20)]
    assert outbox.pending() == 0


def test_a_down_broker_keeps_the_events_and_they_go_when_it_is_back():
    broker = Broker(up=False)
    sender, outbox = durable(broker)
    sender.start()
    for i in range(3):
        sender.publish(event(i))
    time.sleep(0.1)
    assert broker.events == [] and outbox.pending() == 3
    broker.up = True
    assert wait_until(lambda: outbox.pending() == 0)
    sender.stop()
    assert [e.video_ts_sec for e in broker.events] == [0.0, 1.0, 2.0]


def test_what_is_left_at_stop_stays_for_the_next_start():
    outbox = SqliteOutbox(":memory:")
    first = DurablePublisher(outbox, Broker(up=False), retry_min=0.01, retry_max=0.02)
    first.start()
    first.publish(event(7))
    first.stop(drain_timeout=0.05)
    assert outbox.pending() == 1
    broker = Broker()
    second = DurablePublisher(outbox, broker, retry_min=0.01, retry_max=0.02)
    second.start()
    assert wait_until(lambda: outbox.pending() == 0)
    second.stop()
    assert [e.video_ts_sec for e in broker.events] == [7.0]


def test_when_the_outbox_is_full_the_oldest_event_goes():
    broker = Broker()
    sender, outbox = durable(broker, max_events=3)  # not started: nothing drains
    for i in range(5):
        sender.publish(event(i))
    assert sender.dropped == 2
    sender.start()
    sender.stop()
    assert [e.video_ts_sec for e in broker.events] == [2.0, 3.0, 4.0]


def test_a_failing_target_keeps_the_event_and_does_not_end_the_sender():
    class Flaky(Broker):
        failures = 2

        def deliver(self, e):
            if self.failures:
                self.failures -= 1
                raise RuntimeError("broker down")
            return super().deliver(e)

    broker = Flaky()
    sender, outbox = durable(broker)
    sender.start()
    sender.publish(event(0))
    sender.publish(event(1))
    assert wait_until(lambda: outbox.pending() == 0)
    sender.stop()
    assert [e.video_ts_sec for e in broker.events] == [0.0, 1.0]


def test_the_outbox_survives_a_restart_of_the_process(tmp_path):
    path = tmp_path / "outbox" / "events.db"
    first = SqliteOutbox(path)
    sent = ViolationEvent("n1", 4, "no_vest", 0.77, 12.5, b"\xff\xd8jpeg")
    first.add(sent)
    first.close()
    reopened = SqliteOutbox(path)
    assert reopened.pending() == 1
    assert reopened.oldest() == sent  # every field, the snapshot bytes and the time included
    reopened.remove(sent.event_id)
    assert reopened.oldest() is None


def test_adding_the_same_event_twice_keeps_one_copy():
    outbox = SqliteOutbox(":memory:")
    e = event(1)
    outbox.add(e)
    outbox.add(e)
    assert outbox.pending() == 1

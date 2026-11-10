"""Forbidden zones: the geometry, the pipeline's check and alarm, the sync with the cloud's zones, and the alarm adapters."""

import json
import sys
import time

import numpy as np
import pytest
from support import Frame, Pipe

from edge_link import ZoneSpec, ZonesMessage
from edge.application.camera_logic import CameraLogic
from edge.application.zone_book import ZoneBook
from edge.domain.confirmation import Confirmation
from edge.domain.cooldown import Cooldown
from edge.domain.detection import Detection
from edge.domain.event import ZONE_INTRUSION
from edge.domain.zone import Zone, foot_point
from edge.infrastructure.alarm import CommandAlarm, HttpAlarm, MultiAlarm
from edge.infrastructure.zone_sync import ZoneSync

SQUARE = ((0.5, 0.5), (1.0, 0.5), (1.0, 1.0), (0.5, 1.0))  # the lower right quarter of the frame
L_SHAPE = ((0.0, 0.0), (1.0, 0.0), (1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (0.0, 1.0))


def zone(polygon=SQUARE, **kw) -> Zone:
    return Zone(**{"id": 1, "camera_id": 7, "name": "Cẩu tháp", "polygon": polygon, **kw})


# ---------------------------------------------------------------- geometry

@pytest.mark.parametrize("point,inside", [
    ((0.75, 0.75), True), ((0.25, 0.25), False), ((0.75, 0.25), False), ((0.5, 0.75), True),   # on the left edge
    ((1.0, 1.0), True), ((0.49, 0.75), False), ((0.0, 0.0), False),
])
def test_a_point_is_inside_a_square_or_on_its_edge(point, inside):
    assert zone().contains(*point) is inside


def test_a_concave_polygon_is_not_filled_in():
    l_shape = zone(L_SHAPE)
    assert l_shape.contains(0.25, 0.25) and l_shape.contains(0.25, 0.75) and l_shape.contains(0.75, 0.25)
    assert not l_shape.contains(0.75, 0.75)  # the notch of the L


def test_a_person_stands_at_the_bottom_middle_of_their_box_and_never_outside_the_frame():
    assert foot_point((10, 5, 30, 20), 40, 40) == (0.5, 0.5)
    assert foot_point((-10, 0, 100, 90), 40, 40) == (1.0, 1.0)


# ---------------------------------------------------------------- pipeline

class PersonDetector:
    """Finds one person whose box is given in pixels of a 100 x 100 frame."""

    def __init__(self, box, label="person", track_id=4) -> None:
        self.box, self.label, self.track_id = box, label, track_id

    def detect(self, image):
        return [Detection(self.label, 0.88, self.box, self.track_id)]


class Renderer:
    def render(self, image, detections):
        return b"jpeg"


class Sink:
    def __init__(self) -> None:
        self.events = []

    def publish(self, event) -> None:
        self.events.append(event)


class Alarm:
    def __init__(self, fails=False) -> None:
        self.calls, self.fails = [], fails

    def trigger(self, camera_id, reason) -> None:
        self.calls.append((camera_id, reason))
        if self.fails:
            raise RuntimeError("relay stuck")


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


INSIDE = (60, 20, 80, 70)    # feet at (0.7, 0.7): inside the lower right quarter
OUTSIDE = (10, 20, 30, 40)   # feet at (0.2, 0.4)


def watching(detector, zones=(zone(),), alarm=None, min_frames=1, cooldown=10.0, **kw):
    book = ZoneBook()
    book.replace(7, list(zones))
    clock = Clock()
    sink = Sink()
    logic = CameraLogic(
        node_id="n1", camera_id=7, renderer=Renderer(), publisher=sink,
        violation_classes=frozenset({"no_helmet"}), cooldown=Cooldown(5.0), clock=clock,
        zones=book, alarm=alarm, zone_confirmation=Confirmation(min_frames), zone_cooldown=Cooldown(cooldown), **kw,
    )
    return Pipe(logic, detector), sink, clock


def frame():
    return Frame(np.zeros((100, 100, 3), np.uint8), 3.0)


def test_someone_in_a_zone_is_an_event_and_an_alarm():
    alarm = Alarm()
    p, sink, _ = watching(PersonDetector(INSIDE), alarm=alarm)
    assert p.process(frame()) == 1
    event = sink.events[0]
    assert (event.violation_type, event.camera_id, event.node_id) == (ZONE_INTRUSION, 7, "n1")
    assert event.snapshot_jpeg == b"jpeg" and event.confidence == 0.88
    assert alarm.calls == [(7, "Cẩu tháp")]


def test_someone_outside_the_zone_is_nothing():
    alarm = Alarm()
    p, sink, _ = watching(PersonDetector(OUTSIDE), alarm=alarm)
    assert p.process(frame()) == 0 and not sink.events and not alarm.calls


def test_only_the_labels_of_people_count():
    p, sink, _ = watching(PersonDetector(INSIDE, label="no_helmet"))  # a violation of its own, not someone entering
    p.process(frame())
    assert [e.violation_type for e in sink.events] == ["no_helmet"]


def test_a_person_has_to_be_seen_in_the_zone_for_min_frames_before_it_counts():
    p, sink, clock = watching(PersonDetector(INSIDE), min_frames=3)
    assert [p.process(frame()) for _ in range(3)] == [0, 0, 1]


def test_the_alarm_repeats_only_after_the_cooldown_while_the_person_stays():
    alarm = Alarm()
    p, sink, clock = watching(PersonDetector(INSIDE), alarm=alarm, cooldown=10.0)
    p.process(frame())
    clock.now = 4.0
    p.process(frame())
    clock.now = 10.5
    p.process(frame())
    assert len(sink.events) == 2 and len(alarm.calls) == 2


def test_two_people_in_a_zone_each_get_their_own_event():
    class Two:
        def detect(self, image):
            return [Detection("person", 0.9, INSIDE, 1), Detection("person", 0.8, INSIDE, 2)]

    p, sink, _ = watching(Two())
    assert p.process(frame()) == 2


def test_a_switched_off_zone_and_a_camera_without_zones_watch_nothing():
    p, sink, _ = watching(PersonDetector(INSIDE), zones=[zone(enabled=False)])
    assert p.process(frame()) == 0
    p, sink, _ = watching(PersonDetector(INSIDE), zones=[])
    assert p.process(frame()) == 0


def test_a_broken_alarm_does_not_stop_the_event_or_the_camera():
    p, sink, _ = watching(PersonDetector(INSIDE), alarm=Alarm(fails=True))
    assert p.process(frame()) == 1 and len(sink.events) == 1


def test_without_a_zone_book_the_pipeline_behaves_as_before():
    p, sink, _ = watching(PersonDetector(INSIDE))
    p.zones = None
    assert p.process(frame()) == 0


# ---------------------------------------------------------------- sync with the cloud

def message(camera_id=7, enabled=True) -> ZonesMessage:
    return ZonesMessage(camera_id, (ZoneSpec(1, "Hố móng", SQUARE, enabled),))


def test_the_zones_the_cloud_sends_replace_the_old_ones_and_are_kept_on_disk(tmp_path):
    book = ZoneBook()
    sync = ZoneSync(book, tmp_path / "zones.json")
    sync.apply(message())
    assert [z.name for z in book.for_camera(7)] == ["Hố móng"] and book.for_camera(7)[0].camera_id == 7
    sync.apply(ZonesMessage(7, ()))  # an empty message clears the camera
    assert book.for_camera(7) == ()
    assert json.loads((tmp_path / "zones.json").read_text(encoding="utf-8")) == {}


def test_a_restart_without_the_cloud_restores_the_zones_from_disk(tmp_path):
    path = tmp_path / "data" / "zones.json"
    ZoneSync(ZoneBook(), path).apply(message())
    book = ZoneBook()
    assert ZoneSync(book, path).restore() == 1
    assert book.for_camera(7)[0].polygon == SQUARE


def test_a_missing_or_damaged_file_is_no_zones(tmp_path):
    assert ZoneSync(ZoneBook(), tmp_path / "none.json").restore() == 0
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert ZoneSync(ZoneBook(), bad).restore() == 0


def test_the_book_hands_out_only_zones_that_are_switched_on_but_keeps_all():
    book = ZoneBook()
    book.replace(7, [zone(id=1), zone(id=2, enabled=False)])
    assert [z.id for z in book.for_camera(7)] == [1]
    assert [z.id for z in book.snapshot()[7]] == [1, 2]


# ---------------------------------------------------------------- alarms

def test_a_command_alarm_runs_the_command_with_the_camera_and_zone_in_its_environment(tmp_path):
    out = tmp_path / "out.txt"
    code = f"import os; open(r'{out}', 'w', encoding='utf-8').write(os.environ['PPE_ALARM_CAMERA'] + '|' + os.environ['PPE_ALARM_ZONE'])"
    CommandAlarm([sys.executable, "-c", code]).trigger(7, "Cẩu tháp")
    for _ in range(100):
        if out.exists() and out.read_text(encoding="utf-8"):
            break
        time.sleep(0.05)
    assert out.read_text(encoding="utf-8") == "7|Cẩu tháp"


def test_a_command_alarm_does_not_start_a_second_run_while_the_first_is_going():
    alarm = CommandAlarm([sys.executable, "-c", "import time; time.sleep(1.0)"])
    alarm.trigger(1, "a")
    first = alarm._running
    alarm.trigger(1, "a")
    assert alarm._running is first
    first.wait()


def test_a_command_alarm_needs_a_program_and_an_http_alarm_a_url():
    with pytest.raises(ValueError):
        CommandAlarm([])
    with pytest.raises(ValueError):
        HttpAlarm("ftp://siren")


def test_one_failing_alarm_does_not_silence_the_others():
    good = Alarm()
    MultiAlarm([Alarm(fails=True), good]).trigger(7, "x")
    assert good.calls == [(7, "x")]

"""The boxes the edges found, looked up by position in the camera's timeline."""

from edge_link import DetectionBox, DetectionsMessage

from cloud.application.usecases.monitoring_service import MonitoringService
from cloud.infrastructure.detection.detections import DetectionStore
import cv2
import numpy as np
from cloud.infrastructure.detection.feed import Feed
import time
from cloud.application.dto.read_models import Overlay, OverlayBox
from cloud.application.usecases.monitoring_service import blend


def message(ts, *labels, camera=7):
    return DetectionsMessage("n1", camera, ts, 1280, 720, tuple(DetectionBox(l, 0.9, (1, 2, 30, 40), 3) for l in labels))


def test_finds_the_detection_nearest_to_a_position():
    store = DetectionStore()
    store.add(message(10.0, "no_helmet"))
    store.add(message(10.4, "no_vest"))
    assert [b.label for b in store.at(7, 10.04).boxes] == ["no_helmet"]
    assert [b.label for b in store.at(7, 10.38).boxes] == ["no_vest"]


def test_a_position_with_nothing_near_it_has_no_boxes():
    store = DetectionStore()
    store.add(message(10.0, "no_helmet"))
    assert store.at(7, 25.0) is None
    assert store.at(8, 10.0) is None  # another camera


def test_a_later_pass_over_the_same_position_replaces_the_earlier_one():
    store = DetectionStore()
    store.add(message(10.0, "no_helmet"))
    store.add(message(10.02, "no_vest"))  # the video looped
    assert [b.label for b in store.at(7, 10.0).boxes] == ["no_vest"]


def test_what_is_read_carries_the_frame_size_and_the_boxes():
    store = DetectionStore()
    store.add(message(3.0, "person", "no_helmet"))
    overlay = store.at(7, 3.0)
    assert (overlay.width, overlay.height, len(overlay.boxes)) == (1280, 720, 2)
    assert overlay.boxes[0].box == (1, 2, 30, 40) and overlay.boxes[0].track_id == 3


class Feeds:
    def __init__(self, position):
        self._position = position

    def position(self, camera_id):
        return self._position


def monitoring(position, store):
    return MonitoringService(None, Feeds(position), None, None, 9, store)


def test_the_overlay_follows_the_frame_on_screen_not_the_newest_one():
    store = DetectionStore()
    store.add(message(10.0, "no_helmet"))
    store.add(message(10.3, "no_vest"))
    # the feed made the frame at 11.0 s; the viewer sees about 0.7 s behind: 10.3 -> the 10.3 detection
    assert [b.label for b in monitoring(11.0, store).overlay(7).boxes] == ["no_vest"]


def test_a_camera_without_a_feed_has_no_overlay():
    assert monitoring(None, DetectionStore()).overlay(7) is None


def test_a_feed_catches_up_to_the_edge_only_when_it_is_far_off(tmp_path):
    video = tmp_path / "v.avi"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 25, (64, 36))
    for i in range(500):  # twenty seconds
        writer.write(np.full((36, 64, 3), i % 255, np.uint8))
    writer.release()

    feed = Feed(1, tmp_path)
    feed.start()
    deadline = time.time() + 5
    while feed.position_sec is None and time.time() < deadline:
        time.sleep(0.05)
    feed.follow(15.0)  # the edge is at 15 s, this feed near 0: it jumps
    time.sleep(0.5)
    assert feed.position_sec is not None and 14.5 < feed.position_sec < 16.5
    before = feed.position_sec
    feed.follow(feed.position_sec + 0.4)  # within a second: left alone
    time.sleep(0.2)
    assert feed.position_sec - before < 1.0
    feed.stop()


def test_around_gives_the_detections_either_side_of_a_position():
    store = DetectionStore()
    store.add(message(10.0, "no_helmet"))
    store.add(message(10.3, "no_vest"))
    before, after = store.around(7, 10.1)
    assert before.boxes[0].label == "no_helmet" and after.boxes[0].label == "no_vest"
    assert store.around(7, 20.0) == (None, None)


def test_a_frame_between_two_detections_moves_the_boxes_in_proportion():
    one = Overlay(7, 10.0, 100, 100, (OverlayBox("person", 0.9, (0, 0, 10, 10), 1), OverlayBox("person", 0.9, (50, 50, 60, 60), 2)))
    two = Overlay(7, 10.4, 100, 100, (OverlayBox("person", 0.9, (40, 0, 50, 10), 1), OverlayBox("person", 0.9, (80, 80, 90, 90), 3)))
    middle = blend(one, two, 10.1)  # a quarter of the way
    assert [b.box for b in middle.boxes] == [(10, 0, 20, 10)] + [b.box for b in one.boxes[1:]]  # id 1 moved, id 2 only before, id 3 not yet
    late = blend(one, two, 10.3)
    assert [b.track_id for b in late.boxes] == [1, 3]
    assert blend(None, two, 10.1) is two and blend(one, None, 10.1) is one

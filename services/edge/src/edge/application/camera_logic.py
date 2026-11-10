"""One camera: detections in, violation events out.

The stream (DeepStream) reads the camera, runs the model and tracks the objects; this holds what the system decides from
them: when a violation is confirmed, when it may be reported again, and who is standing in a forbidden zone."""

import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from edge.application.ports import AlarmSink, DetectionPublisher, EventPublisher, SnapshotRenderer
from edge.application.zone_book import ZoneBook
from edge.domain.confirmation import Confirmation
from edge.domain.cooldown import Cooldown
from edge.domain.detection import Detection
from edge.domain.event import ZONE_INTRUSION, ViolationEvent
from edge.domain.zone import foot_point

log = logging.getLogger("edge.camera")
_FPS_WINDOW_SEC = 3.0  # the detections per second are counted over this long


@dataclass
class CameraLogic:
    node_id: str
    camera_id: int
    renderer: SnapshotRenderer
    publisher: EventPublisher
    violation_classes: frozenset[str]
    cooldown: Cooldown
    confirmation: Confirmation = field(default_factory=Confirmation)  # by default one sighting is enough
    detection_sink: DetectionPublisher | None = None  # gets every box of every detection, not only the violations
    zones: ZoneBook | None = None  # the zones no one may enter; without one, none are watched
    alarm: AlarmSink | None = None  # sounds on the spot when someone enters a zone
    zone_classes: frozenset[str] = frozenset({"person"})  # what counts as someone: the labels the zones watch
    zone_confirmation: Confirmation = field(default_factory=Confirmation)  # sightings inside a zone before it counts
    zone_cooldown: Cooldown = field(default_factory=lambda: Cooldown(10.0))  # an alarm repeats at most this often while they stay
    clock: Callable[[], float] = time.monotonic
    fps: float = field(default=0.0, init=False)  # detections per second over the last few seconds
    _done: deque = field(default_factory=lambda: deque(maxlen=64), init=False, repr=False)  # when the last detections arrived

    def handle(self, ts_sec: float, width: int, height: int, detections: list[Detection], get_image: Callable[[], np.ndarray]) -> int:
        """Looks at the detections of one frame; returns how many events it published. The picture is fetched through
        `get_image` only when an event needs it, because it lives on the GPU."""
        self._measure()
        if self.detection_sink is not None:
            self.detection_sink.publish_detections(self.camera_id, ts_sec, width, height, detections, self.fps, 0.0, 0)
        sent, now, snapshot = 0, self.clock(), None
        for d in detections:
            if d.label not in self.violation_classes:
                continue
            key = d.label if d.track_id is None else f"{d.track_id}:{d.label}"  # one violation of one person
            if not self.confirmation.confirm(key, now) or not self.cooldown.allow(key, now):
                continue
            snapshot = snapshot or self.renderer.render(get_image(), detections)  # one image per frame, shared by its events
            self.publisher.publish(ViolationEvent(
                node_id=self.node_id, camera_id=self.camera_id, violation_type=d.label,
                confidence=d.confidence, video_ts_sec=ts_sec, snapshot_jpeg=snapshot,
            ))
            sent += 1
        if self.zones is not None:
            sent += self._watch_zones(ts_sec, width, height, detections, get_image, now, snapshot)
        return sent

    def _watch_zones(
        self, ts_sec: float, width: int, height: int, detections: list[Detection], get_image: Callable[[], np.ndarray],
        now: float, snapshot: bytes | None,
    ) -> int:
        """An event and an alarm for everyone whose feet are inside a zone. A person is told apart by the track the tracker
        gave them, so the confirmation and the cooldown are per person and per zone."""
        zones = self.zones.for_camera(self.camera_id)
        if not zones:
            return 0
        sent = 0
        for d in detections:
            if d.label not in self.zone_classes:
                continue
            x, y = foot_point(d.box, width, height)
            for zone in zones:
                if not zone.contains(x, y):
                    continue
                key = f"zone:{zone.id}:{d.track_id if d.track_id is not None else '-'}"
                if not self.zone_confirmation.confirm(key, now) or not self.zone_cooldown.allow(key, now):
                    continue
                snapshot = snapshot or self.renderer.render(get_image(), detections)
                self.publisher.publish(ViolationEvent(
                    node_id=self.node_id, camera_id=self.camera_id, violation_type=ZONE_INTRUSION,
                    confidence=d.confidence, video_ts_sec=ts_sec, snapshot_jpeg=snapshot,
                ))
                self._sound(zone.name)
                sent += 1
        return sent

    def _sound(self, zone_name: str) -> None:
        if self.alarm is None:
            return
        try:
            self.alarm.trigger(self.camera_id, zone_name)
        except Exception:  # an alarm that breaks must not stop the camera's detection
            log.exception("the alarm of camera %s failed", self.camera_id)

    def _measure(self) -> None:
        """Keeps the speed of the stream for this camera: how many detections a second."""
        now = self.clock()
        self._done.append(now)
        window = [t for t in self._done if now - t <= _FPS_WINDOW_SEC]
        self.fps = (len(window) - 1) / (window[-1] - window[0]) if len(window) > 1 and window[-1] > window[0] else 0.0

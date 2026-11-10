"""One camera: frames in, violation events out.

The camera is read at its own pace and the detector looks at the newest frame whenever it is free, so what it finds is
always about what the camera shows now. A detector slower than the camera drops frames; it never falls behind."""

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from edge.application.latest_frame import LatestFrame
from edge.application.ports import (
    AlarmSink, DetectionPublisher, Detector, EventPublisher, Frame, FrameSource, SnapshotRenderer, Tracker,
)
from edge.application.zone_book import ZoneBook
from edge.domain.confirmation import Confirmation
from edge.domain.cooldown import Cooldown
from edge.domain.detection import Detection
from edge.domain.event import ZONE_INTRUSION, ViolationEvent
from edge.domain.zone import foot_point

log = logging.getLogger("edge.pipeline")
_FPS_WINDOW_SEC = 3.0  # the detections per second are counted over this long


@dataclass
class CameraPipeline:
    node_id: str
    camera_id: int
    source: FrameSource
    detector: Detector
    renderer: SnapshotRenderer
    publisher: EventPublisher
    violation_classes: frozenset[str]
    every_n: int  # at most one detection per every_n frames the camera produces (the detector may skip more)
    cooldown: Cooldown
    tracker: Tracker | None = None  # without one a violation is told apart by its label only
    confirmation: Confirmation = field(default_factory=Confirmation)  # by default one sighting is enough
    detection_sink: DetectionPublisher | None = None  # gets every box of every detection, not only the violations
    zones: ZoneBook | None = None  # the zones no one may enter; without one, none are watched
    alarm: AlarmSink | None = None  # sounds on the spot when someone enters a zone
    zone_classes: frozenset[str] = frozenset({"person"})  # what counts as someone: the labels the zones watch
    zone_confirmation: Confirmation = field(default_factory=Confirmation)  # sightings inside a zone before it counts
    zone_cooldown: Cooldown = field(default_factory=lambda: Cooldown(10.0))  # an alarm repeats at most this often while they stay
    clock: Callable[[], float] = time.monotonic
    dropped: int = field(default=0, init=False)  # frames the detector had no time for
    fps: float = field(default=0.0, init=False)  # detections per second over the last few seconds
    infer_ms: float = field(default=0.0, init=False)  # milliseconds one detection takes (smoothed)
    _done: deque = field(default_factory=lambda: deque(maxlen=64), init=False, repr=False)  # when the last detections ended

    def process(self, frame: Frame) -> int:
        """Looks at one frame; returns how many events it published."""
        started = self.clock()
        detections = self.detector.detect(frame.image)
        self._measure(started)
        if self.tracker is not None:
            detections = self.tracker.update(detections)
        if self.detection_sink is not None:
            height, width = frame.image.shape[:2]
            self.detection_sink.publish_detections(
                self.camera_id, frame.ts_sec, width, height, detections, self.fps, self.infer_ms, self.dropped,
            )
        sent, now, snapshot = 0, self.clock(), None
        for d in detections:
            if d.label not in self.violation_classes:
                continue
            key = d.label if d.track_id is None else f"{d.track_id}:{d.label}"  # one violation of one person
            if not self.confirmation.confirm(key, now) or not self.cooldown.allow(key, now):
                continue
            snapshot = snapshot or self.renderer.render(frame.image, detections)  # one image per frame, shared by its events
            self.publisher.publish(ViolationEvent(
                node_id=self.node_id, camera_id=self.camera_id, violation_type=d.label,
                confidence=d.confidence, video_ts_sec=frame.ts_sec, snapshot_jpeg=snapshot,
            ))
            sent += 1
        if self.zones is not None:
            sent += self._watch_zones(frame, detections, now, snapshot)
        return sent

    def _watch_zones(self, frame: Frame, detections: list[Detection], now: float, snapshot: bytes | None) -> int:
        """An event and an alarm for everyone whose feet are inside a zone. A person is told apart by the track the tracker
        gave them, so the confirmation and the cooldown are per person and per zone."""
        zones = self.zones.for_camera(self.camera_id)
        if not zones:
            return 0
        height, width = frame.image.shape[:2]
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
                snapshot = snapshot or self.renderer.render(frame.image, detections)
                self.publisher.publish(ViolationEvent(
                    node_id=self.node_id, camera_id=self.camera_id, violation_type=ZONE_INTRUSION,
                    confidence=d.confidence, video_ts_sec=frame.ts_sec, snapshot_jpeg=snapshot,
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

    def _measure(self, started: float) -> None:
        """Keeps the speed of the detector: how many detections a second, and how long one takes."""
        now = self.clock()
        took = (now - started) * 1000
        self.infer_ms = took if self.infer_ms == 0.0 else self.infer_ms * 0.8 + took * 0.2
        self._done.append(now)
        window = [t for t in self._done if now - t <= _FPS_WINDOW_SEC]
        self.fps = (len(window) - 1) / (window[-1] - window[0]) if len(window) > 1 and window[-1] > window[0] else 0.0

    def run(self, stop: threading.Event) -> None:
        """Reads the camera in this thread and detects in another, joined by a one-frame slot. Raises what either
        side raised."""
        slot = LatestFrame()
        failure: list[Exception] = []
        worker = threading.Thread(target=self._detect, args=(slot, stop, failure), name=f"detect-{self.camera_id}", daemon=True)
        worker.start()
        try:
            for frame in self.source.frames():
                if stop.is_set() or failure:
                    break
                slot.put(frame)
        finally:
            slot.close()
            worker.join()
        if failure:
            raise failure[0]

    def _detect(self, slot: LatestFrame, stop: threading.Event, failure: list[Exception]) -> None:
        last = -self.every_n  # so the first frame qualifies
        try:
            while not stop.is_set():
                item = slot.take(last + self.every_n)
                if item is None:
                    if slot.closed:
                        return
                    continue
                index, frame = item
                self.dropped += max(0, index - last - self.every_n) if last >= 0 else 0
                last = index
                self.process(frame)
        except Exception as error:  # the reader stops on it and run() raises it
            failure.append(error)

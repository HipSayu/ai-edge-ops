"""The boxes the edges found, kept by position in the camera's timeline so the web can draw the ones that belong to the
frame it is showing.

The edge detects on the frame at position t of its video and the cloud shows the frame at position t' of the same
video: the two clocks differ by a constant, so they are matched by position, not by arrival time. Positions are kept
in tenths of a second; a later pass over the same position replaces the earlier one."""

import threading
import time
from collections import OrderedDict

from edge_link import DetectionsMessage

from cloud.application.dto.read_models import Overlay, OverlayBox

_BUCKET_SEC = 0.1
_REACH = 3  # buckets either side of the wanted position that still count as "that frame"
_KEEP = 20_000  # positions per camera: more than half an hour of video at ten detections a second
_ONLINE_MAX_AGE_SEC = 10.0  # no detection for longer than this and the camera counts as unavailable


class DetectionStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cameras: dict[int, OrderedDict[int, Overlay]] = {}
        self._speed: dict[int, tuple[float, float, int]] = {}  # camera -> (detections/s, ms per detection, frames dropped)
        self._last_seen: dict[int, float] = {}  # camera -> monotonic time of its last detection message

    def add(self, message: DetectionsMessage) -> None:
        boxes = tuple(OverlayBox(b.label, b.confidence, b.box, b.track_id) for b in message.boxes)
        overlay = Overlay(message.camera_id, message.video_ts_sec, message.width, message.height, boxes)
        bucket = round(message.video_ts_sec / _BUCKET_SEC)
        with self._lock:
            self._speed[message.camera_id] = (message.fps, message.infer_ms, message.dropped)
            self._last_seen[message.camera_id] = time.monotonic()
            frames = self._cameras.setdefault(message.camera_id, OrderedDict())
            frames.pop(bucket, None)  # re-inserted last: the oldest to go is the one longest unseen
            frames[bucket] = overlay
            while len(frames) > _KEEP:
                frames.popitem(last=False)

    def at(self, camera_id: int, position_sec: float) -> Overlay | None:
        """The boxes of the detection closest to `position_sec`, or None when there is none near it."""
        wanted = round(position_sec / _BUCKET_SEC)
        with self._lock:
            frames = self._cameras.get(camera_id)
            if not frames:
                return None
            for distance in range(_REACH + 1):
                for bucket in (wanted - distance, wanted + distance):
                    if bucket in frames:
                        return frames[bucket]
        return None

    def around(self, camera_id: int, position_sec: float) -> tuple[Overlay | None, Overlay | None]:
        """The latest detection at or before a position and the earliest at or after it (within the same reach as `at`),
        for the boxes of a frame between two detections to be worked out from both."""
        centre = round(position_sec / _BUCKET_SEC)
        before = after = None
        with self._lock:
            frames = self._cameras.get(camera_id) or {}
            for bucket in range(centre - _REACH, centre + _REACH + 1):
                found = frames.get(bucket)
                if found is None:
                    continue
                if found.position_sec <= position_sec and (before is None or found.position_sec > before.position_sec):
                    before = found
                if found.position_sec >= position_sec and (after is None or found.position_sec < after.position_sec):
                    after = found
        return before, after

    def speed(self, camera_id: int) -> tuple[float, float, int] | None:
        """How fast the edge is detecting on this camera: (detections per second, ms per detection, frames dropped)."""
        with self._lock:
            return self._speed.get(camera_id)

    def online(self, camera_id: int) -> bool:
        """Whether the edge has sent a detection for this camera within `_ONLINE_MAX_AGE_SEC`."""
        with self._lock:
            seen = self._last_seen.get(camera_id)
        return seen is not None and time.monotonic() - seen <= _ONLINE_MAX_AGE_SEC

    def forget(self, camera_id: int) -> None:
        with self._lock:
            self._speed.pop(camera_id, None)
            self._last_seen.pop(camera_id, None)
            self._cameras.pop(camera_id, None)

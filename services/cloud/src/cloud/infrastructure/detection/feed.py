"""One simulated live camera: loops its videos and keeps the latest frame. Detection runs on the edge."""

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import cv2

from cloud.infrastructure.files.video_store import list_videos
from cloud.infrastructure.detection.render import encode_jpeg, placeholder_jpeg


_START_AGE_SEC = 0.7  # a new viewer is first sent frames no older than this
_RING = 75  # frames kept for the viewers: a few seconds
_RESYNC_SEC = 1.0  # a feed this far from the edge's position jumps to it; closer is left alone


@dataclass
class Feed:
    camera_id: int
    folder: Path
    latest_jpeg: bytes = b""
    position_sec: float | None = None  # of the frame in latest_jpeg, in the video it came from
    _follow: float | None = None
    _ring: deque = field(default_factory=lambda: deque(maxlen=_RING))  # (seq, made at, position, jpeg), oldest first
    _seq: int = 0
    _stop: threading.Event = field(default_factory=threading.Event)

    def start(self) -> None:
        threading.Thread(target=self._run, name=f"feed-{self.camera_id}", daemon=True).start()

    def stop(self) -> None:
        self._stop.set()

    def _publish(self, jpeg: bytes, position: float | None) -> None:
        self.latest_jpeg, self.position_sec = jpeg, position
        self._seq += 1
        self._ring.append((self._seq, time.monotonic(), position, jpeg))

    def frame_after(self, seq: int) -> tuple[int, float, float | None, bytes] | None:
        """The oldest frame still kept that is newer than `seq`, as (seq, seconds since it was made, position, jpeg)."""
        now = time.monotonic()
        for entry in list(self._ring):
            # seq 0 is a viewer that has just arrived: it starts from the present, not from the whole backlog
            if entry[0] > seq and (seq > 0 or now - entry[1] < _START_AGE_SEC):
                return entry[0], time.monotonic() - entry[1], entry[2], entry[3]
        return None

    def follow(self, position_sec: float) -> None:
        """The edge says where its video is. The cloud only plays a stand-in for the camera, so the edge's clock is the
        camera's: the feed catches up to it (once, when it is off by more than a second), and from then on the boxes
        the edge sends belong to the frames shown here. Assumes one video per camera."""
        self._follow = position_sec

    def _run(self) -> None:
        while not self._stop.is_set():
            videos = list_videos(self.folder)
            if not videos:
                self._publish(placeholder_jpeg("No video uploaded"), None)
                self._stop.wait(2.0)
                continue
            for name in videos:  # name order, then loop forever
                if self._stop.is_set():
                    return
                self._play(self.folder / name)

    def _play(self, path: Path) -> None:
        cap = cv2.VideoCapture(str(path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        delay = 1.0 / min(fps, 30.0)
        index = 0
        try:
            while not self._stop.is_set():
                started = time.monotonic()
                target, self._follow = self._follow, None
                if target is not None and abs(target - index / fps) > _RESYNC_SEC:
                    index = int(target * fps)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
                ok, frame = cap.read()
                if not ok:
                    return
                self._publish(encode_jpeg(frame), index / fps)  # the position is the measure the edge puts on its detections
                index += 1
                self._stop.wait(max(0.0, delay - (time.monotonic() - started)))
        finally:
            cap.release()

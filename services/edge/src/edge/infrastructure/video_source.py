"""A FrameSource over video files: plays them in name order at their own speed, and starts over when they end.

It stands in for a live camera on a machine without one. A real camera (RTSP, a device) is another FrameSource."""

import time
from collections.abc import Iterator
from pathlib import Path

import cv2

from edge.application.ports import Frame

_SUFFIXES = {".mp4", ".avi", ".mkv", ".mov"}


class VideoFileSource:
    def __init__(self, path: Path, loop: bool = True, max_fps: float = 30.0) -> None:
        self._path, self._loop, self._max_fps = path, loop, max_fps

    def _files(self) -> list[Path]:
        if self._path.is_file():
            return [self._path]
        return sorted(p for p in self._path.glob("*") if p.suffix.lower() in _SUFFIXES) if self._path.is_dir() else []

    def frames(self) -> Iterator[Frame]:
        while True:
            files = self._files()
            if not files:
                raise FileNotFoundError(f"no video at {self._path}")
            for file in files:
                yield from self._play(file)
            if not self._loop:
                return

    def _play(self, file: Path) -> Iterator[Frame]:
        cap = cv2.VideoCapture(str(file))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        delay = 1.0 / min(fps, self._max_fps)
        index = 0
        begun = time.monotonic()
        try:
            while True:
                ok, image = cap.read()
                if not ok:
                    return
                yield Frame(image, index / fps)
                index += 1
                # on a schedule from the start, not "delay after each frame": the time spent decoding and handing over
                # a frame does not add up into a video that plays slower than it should
                ahead = begun + index * delay - time.monotonic()
                if ahead > 0:
                    time.sleep(ahead)
                elif ahead < -1.0:  # more than a second behind (a stall): carry on from now instead of racing to catch up
                    begun -= ahead
        finally:
            cap.release()

"""The hand-over between a camera's reader and its detector: one slot that always holds the newest frame."""

import threading

from edge.application.ports import Frame


class LatestFrame:
    """A frame nobody has taken is replaced by the next one, so the detector never works through a backlog: it takes
    whatever the camera shows now, and the frames it was too busy for are dropped, as a live camera would."""

    def __init__(self) -> None:
        self._changed = threading.Condition()
        self._frame: Frame | None = None
        self._index = -1  # of the frame in the slot: the n-th the camera produced
        self._closed = False

    def put(self, frame: Frame) -> None:
        with self._changed:
            self._index += 1
            self._frame = frame
            self._changed.notify_all()

    def close(self) -> None:
        """The camera has no more frames."""
        with self._changed:
            self._closed = True
            self._changed.notify_all()

    @property
    def closed(self) -> bool:
        return self._closed

    def take(self, min_index: int, timeout: float = 0.5) -> tuple[int, Frame] | None:
        """Waits for a frame with index >= min_index and returns it with its index (the newest, not the first one to
        qualify). None when none came within `timeout`, or the camera ended without one."""
        with self._changed:
            self._changed.wait_for(lambda: self._index >= min_index or self._closed, timeout)
            if self._index >= min_index and self._frame is not None:
                return self._index, self._frame
            return None

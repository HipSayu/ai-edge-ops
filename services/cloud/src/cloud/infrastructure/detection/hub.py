import threading
from pathlib import Path

from cloud.infrastructure.detection.feed import Feed


class FeedHub:
    """The FeedControl port. Starts one feed per camera on demand and hands out its latest frame."""

    def __init__(self) -> None:
        self._feeds: dict[int, Feed] = {}
        self._lock = threading.Lock()

    def ensure(self, camera_id: int, folder: Path) -> None:
        with self._lock:
            if camera_id not in self._feeds:
                feed = Feed(camera_id, folder)
                self._feeds[camera_id] = feed
                feed.start()

    def drop(self, camera_id: int) -> None:
        with self._lock:
            feed = self._feeds.pop(camera_id, None)
        if feed:
            feed.stop()

    def person_count(self, camera_id: int) -> int:
        return 0  # people are counted on the edge; the cloud does not run detection

    def latest_frame(self, camera_id: int) -> bytes:
        feed = self._feeds.get(camera_id)
        return feed.latest_jpeg if feed else b""

    def frame_after(self, camera_id: int, seq: int) -> tuple[int, float, float | None, bytes] | None:
        feed = self._feeds.get(camera_id)
        return feed.frame_after(seq) if feed else None

    def follow(self, camera_id: int, position_sec: float) -> None:
        feed = self._feeds.get(camera_id)
        if feed:
            feed.follow(position_sec)

    def position(self, camera_id: int) -> float | None:
        feed = self._feeds.get(camera_id)
        return feed.position_sec if feed else None

    def stop_all(self) -> None:
        with self._lock:
            feeds, self._feeds = list(self._feeds.values()), {}
        for feed in feeds:
            feed.stop()

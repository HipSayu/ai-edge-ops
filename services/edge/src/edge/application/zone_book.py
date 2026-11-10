"""The zones of the cameras this node runs. The link thread replaces them when the cloud sends new ones, the camera
threads read them for every detection, so every access goes through one lock."""

import threading

from edge.domain.zone import Zone


class ZoneBook:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._zones: dict[int, tuple[Zone, ...]] = {}

    def replace(self, camera_id: int, zones: list[Zone] | tuple[Zone, ...]) -> None:
        with self._lock:
            if zones:
                self._zones[camera_id] = tuple(zones)
            else:
                self._zones.pop(camera_id, None)

    def for_camera(self, camera_id: int) -> tuple[Zone, ...]:
        """The zones of a camera that are switched on."""
        with self._lock:
            return tuple(z for z in self._zones.get(camera_id, ()) if z.enabled)

    def snapshot(self) -> dict[int, tuple[Zone, ...]]:
        """Every zone, switched on or not, to keep on disk."""
        with self._lock:
            return dict(self._zones)

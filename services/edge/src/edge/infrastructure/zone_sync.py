"""Keeps the node's zones current: takes what the cloud sends, applies it to the ZoneBook, and keeps a copy on disk so a node
that restarts while the cloud is out of reach still knows its zones."""

import json
import logging
import os
from pathlib import Path

from edge_link import ZonesMessage

from edge.application.zone_book import ZoneBook
from edge.domain.zone import Zone

log = logging.getLogger("edge.zones")


class ZoneSync:
    def __init__(self, book: ZoneBook, path: Path) -> None:
        self._book, self._path = book, Path(path)

    def restore(self) -> int:
        """Loads the zones kept on disk into the book. Returns how many zones there are; a missing or damaged file is no zones."""
        try:
            body = json.loads(self._path.read_text(encoding="utf-8"))
            count = 0
            for camera_id, zones in body.items():
                loaded = [Zone(int(z["id"]), int(camera_id), str(z["name"]), tuple((float(x), float(y)) for x, y in z["polygon"]),
                               bool(z.get("enabled", True))) for z in zones]
                self._book.replace(int(camera_id), loaded)
                count += len(loaded)
            return count
        except FileNotFoundError:
            return 0
        except (ValueError, KeyError, TypeError, OSError):
            log.warning("could not read the zones kept in %s; starting without them", self._path)
            return 0

    def apply(self, message: ZonesMessage) -> None:
        """The cloud's zones for one camera replace the ones the node had; the new state is written to disk."""
        self._book.replace(message.camera_id, [
            Zone(z.id, message.camera_id, z.name, z.polygon, z.enabled) for z in message.zones
        ])
        self._save()
        log.info("camera %s: %d zone(s)", message.camera_id, len(message.zones))

    def _save(self) -> None:
        body = {
            str(camera_id): [{"id": z.id, "name": z.name, "enabled": z.enabled, "polygon": [list(c) for c in z.polygon]} for z in zones]
            for camera_id, zones in self._book.snapshot().items()
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(json.dumps(body), encoding="utf-8")
        os.replace(tmp, self._path)  # a power cut leaves the old file or the new one, never half of one

"""The EventOutbox port over SQLite: one file, written before an event is sent and emptied when the broker acknowledges."""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from edge.domain.event import ViolationEvent


class SqliteOutbox:
    """Oldest first. Bounded: past `max_events` the oldest are dropped, since a stale violation is worth less than the
    one that just happened (and a long outage must not fill the device's disk with snapshots)."""

    def __init__(self, path: Path | str, max_events: int = 500) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._max = max_events
        self._lock = threading.Lock()  # cameras add, the sender thread reads and removes
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")  # a power cut may lose the last write, never corrupt the file
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS events ("
            "seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL, node_id TEXT NOT NULL, "
            "camera_id INTEGER NOT NULL, violation_type TEXT NOT NULL, confidence REAL NOT NULL, "
            "video_ts_sec REAL NOT NULL, occurred_at TEXT NOT NULL, snapshot BLOB NOT NULL)"
        )
        self._db.commit()

    def add(self, event: ViolationEvent) -> int:
        with self._lock, self._db:
            self._db.execute(
                "INSERT OR IGNORE INTO events (event_id, node_id, camera_id, violation_type, confidence, video_ts_sec, "
                "occurred_at, snapshot) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (event.event_id, event.node_id, event.camera_id, event.violation_type, event.confidence,
                 event.video_ts_sec, event.occurred_at.isoformat(), event.snapshot_jpeg),
            )
            excess = self._db.execute("SELECT COUNT(*) FROM events").fetchone()[0] - self._max
            if excess > 0:
                self._db.execute("DELETE FROM events WHERE seq IN (SELECT seq FROM events ORDER BY seq LIMIT ?)", (excess,))
            return max(excess, 0)

    def oldest(self) -> ViolationEvent | None:
        with self._lock:
            row = self._db.execute(
                "SELECT event_id, node_id, camera_id, violation_type, confidence, video_ts_sec, occurred_at, snapshot "
                "FROM events ORDER BY seq LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        event_id, node_id, camera_id, violation_type, confidence, video_ts_sec, occurred_at, snapshot = row
        return ViolationEvent(
            node_id, camera_id, violation_type, confidence, video_ts_sec, bytes(snapshot),
            event_id=event_id, occurred_at=datetime.fromisoformat(occurred_at),
        )

    def remove(self, event_id: str) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM events WHERE event_id = ?", (event_id,))

    def pending(self) -> int:
        with self._lock:
            return self._db.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def close(self) -> None:
        with self._lock:
            self._db.close()

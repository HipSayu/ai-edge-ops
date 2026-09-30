import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np

_SCHEMA = """
CREATE TABLE IF NOT EXISTS outbox (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT NOT NULL,
    channel TEXT NOT NULL,          -- telemetry | event
    kind    TEXT NOT NULL,
    payload TEXT NOT NULL,
    sent    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_outbox_pending ON outbox(sent, id);
CREATE INDEX IF NOT EXISTS idx_outbox_ts ON outbox(ts);
CREATE TABLE IF NOT EXISTS alarm_windows (
    ts     TEXT NOT NULL,
    risk   REAL NOT NULL,
    shape  TEXT NOT NULL,           -- "rows,cols"
    window BLOB NOT NULL            -- float32, row-major
);
"""


class SqliteHealthStore:
    """HealthStore on a local SQLite file (WAL): survives agent restarts and power loss."""

    def __init__(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")
        self._db.executescript(_SCHEMA)

    def enqueue(self, channel: str, kind: str, payload: str, at: datetime) -> None:
        self._db.execute("INSERT INTO outbox (ts, channel, kind, payload) VALUES (?, ?, ?, ?)",
                         (at.isoformat(), channel, kind, payload))

    def pending(self, limit: int) -> list[tuple[int, str, str, str]]:
        return self._db.execute(
            "SELECT id, channel, kind, payload FROM outbox WHERE sent = 0 ORDER BY id LIMIT ?", (limit,)
        ).fetchall()

    def mark_sent(self, ids: list[int]) -> None:
        self._db.executemany("UPDATE outbox SET sent = 1 WHERE id = ?", [(i,) for i in ids])

    def save_alarm_window(self, at: datetime, risk: float, window: np.ndarray) -> None:
        w = np.ascontiguousarray(window, dtype=np.float32)
        self._db.execute("INSERT INTO alarm_windows (ts, risk, shape, window) VALUES (?, ?, ?, ?)",
                         (at.isoformat(), risk, f"{w.shape[0]},{w.shape[1]}", w.tobytes()))

    def prune(self, older_than: datetime, max_rows: int) -> None:
        """Drop old rows, then cap the outbox size (oldest first, unsent included: disk beats backlog)."""
        cutoff = older_than.isoformat()
        self._db.execute("DELETE FROM outbox WHERE ts < ?", (cutoff,))
        self._db.execute("DELETE FROM alarm_windows WHERE ts < ?", (cutoff,))
        self._db.execute(
            "DELETE FROM outbox WHERE id <= (SELECT id FROM outbox ORDER BY id DESC LIMIT 1 OFFSET ?)", (max_rows,)
        )

    def close(self) -> None:
        self._db.close()

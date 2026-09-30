from datetime import datetime
from typing import Protocol

import numpy as np


class HealthStore(Protocol):
    """Local durable outbox for health messages (store-and-forward while the broker is unreachable)."""

    def enqueue(self, channel: str, kind: str, payload: str, at: datetime) -> None:
        """channel = "telemetry" | "event"; kind = topic kind; payload = JSON body."""
        ...

    def pending(self, limit: int) -> list[tuple[int, str, str, str]]:
        """Oldest unsent messages as (id, channel, kind, payload)."""
        ...

    def mark_sent(self, ids: list[int]) -> None: ...

    def save_alarm_window(self, at: datetime, risk: float, window: np.ndarray) -> None:
        """Keep the model input that raised an alarm, for later debugging."""
        ...

    def prune(self, older_than: datetime, max_rows: int) -> None: ...

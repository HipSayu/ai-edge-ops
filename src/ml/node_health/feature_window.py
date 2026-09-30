"""Rolling input window built from live samples with the same preprocessing as training."""

from collections import deque
from collections.abc import Mapping

import numpy as np


class FeatureWindow:
    """Keeps the last `size` rows: forward-fills gaps per feature, turns cumulative counters into per-step
    deltas (clipped at 0 so an agent restart doesn't produce a negative spike)."""

    def __init__(self, features: list[str], size: int, counters: list[str] = ()) -> None:
        self.features = list(features)
        self.size = size
        self._counter_idx = [self.features.index(k) for k in counters if k in self.features]
        self._rows: deque[np.ndarray] = deque(maxlen=size)
        self._last = np.full(len(self.features), np.nan, dtype=np.float32)  # last seen value (for ffill)
        self._last_counter = np.full(len(self.features), np.nan, dtype=np.float32)

    def push(self, sample: Mapping[str, float | int | None]) -> np.ndarray:
        raw = np.array([np.nan if sample.get(k) is None else float(sample[k]) for k in self.features], dtype=np.float32)
        row = np.where(np.isnan(raw), self._last, raw)
        self._last = row.copy()
        for j in self._counter_idx:
            prev, self._last_counter[j] = self._last_counter[j], row[j]
            row[j] = 0.0 if np.isnan(prev) or np.isnan(row[j]) else max(0.0, row[j] - prev)
        self._rows.append(row)
        return row

    @property
    def ready(self) -> bool:
        return len(self._rows) == self.size

    def matrix(self) -> np.ndarray:
        """[size, features] raw (unnormalized) window; only meaningful once `ready`."""
        return np.stack(self._rows)

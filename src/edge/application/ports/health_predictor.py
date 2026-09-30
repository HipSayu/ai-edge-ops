from typing import Protocol

import numpy as np


class HealthPredictor(Protocol):
    """A loaded early-warning model: its input contract plus a scorer for one raw window."""

    version: str
    features: list[str]
    counters: list[str]  # cumulative counters the model expects as per-step deltas
    window: int
    threshold: float
    alarm_consecutive: int
    horizon_sec: float

    def score(self, window: np.ndarray) -> float:
        """Raw (unnormalized) [window, features] → P(degradation within horizon_sec)."""
        ...

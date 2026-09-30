"""Turns a stream of risk scores into alarm raise/clear transitions (debounced both ways)."""

from enum import StrEnum


class AlarmTransition(StrEnum):
    RAISED = "raised"
    CLEARED = "cleared"


class AlarmTracker:
    """Raise after `raise_after` consecutive scores ≥ threshold; clear after `clear_after` consecutive scores
    below `threshold × clear_ratio` (hysteresis keeps a score hovering at the threshold from flapping)."""

    def __init__(self, threshold: float, raise_after: int = 3, clear_after: int = 12, clear_ratio: float = 0.8) -> None:
        self.threshold = threshold
        self._raise_after = raise_after
        self._clear_after = clear_after
        self._clear_below = threshold * clear_ratio
        self._above = 0
        self._below = 0
        self.active = False
        self.peak = 0.0

    def update(self, risk: float) -> AlarmTransition | None:
        if not self.active:
            self._above = self._above + 1 if risk >= self.threshold else 0
            if self._above >= self._raise_after:
                self.active, self._below, self.peak = True, 0, risk
                return AlarmTransition.RAISED
            return None
        self.peak = max(self.peak, risk)
        self._below = self._below + 1 if risk < self._clear_below else 0
        if self._below >= self._clear_after:
            self.active, self._above = False, 0
            return AlarmTransition.CLEARED
        return None

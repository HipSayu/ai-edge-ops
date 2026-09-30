from pathlib import Path

import numpy as np

from src.ml.node_health import HealthModel


class NumpyHealthPredictor:
    """HealthPredictor backed by an exported model directory (meta.json + weights.npz)."""

    def __init__(self, model_dir: str | Path) -> None:
        self._model = HealthModel.load(model_dir)
        m = self._model
        self.version, self.features, self.counters = m.version, m.features, m.counters
        self.window, self.threshold, self.alarm_consecutive = m.window, m.threshold, m.alarm_consecutive
        self.horizon_sec = m.horizon_sec

    def score(self, window: np.ndarray) -> float:
        return float(self._model.predict(window)[0])

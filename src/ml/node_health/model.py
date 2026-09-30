"""The trained LSTM, re-implemented as a numpy forward pass (PyTorch gate order i, f, g, o)."""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

META_FILE = "meta.json"
WEIGHTS_FILE = "weights.npz"


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


@dataclass(frozen=True)
class HealthModel:
    version: str
    features: list[str]
    counters: list[str]  # cumulative counters fed to the model as per-step deltas
    mean: np.ndarray
    std: np.ndarray
    window: int
    horizon_sec: float
    sample_sec: float
    threshold: float
    alarm_consecutive: int
    weights: dict[str, np.ndarray]
    layers: int

    @classmethod
    def load(cls, directory: str | Path) -> "HealthModel":
        directory = Path(directory)
        meta = json.loads((directory / META_FILE).read_text(encoding="utf-8"))
        with np.load(directory / WEIGHTS_FILE) as npz:
            weights = {k: npz[k].astype(np.float32) for k in npz.files}
        return cls(
            version=meta["version"],
            features=list(meta["features"]),
            counters=list(meta.get("counters_as_delta", [])),
            mean=np.asarray(meta["mean"], dtype=np.float32),
            std=np.asarray(meta["std"], dtype=np.float32),
            window=int(meta["window"]),
            horizon_sec=float(meta["horizon"]) * float(meta["sample_sec"]),
            sample_sec=float(meta["sample_sec"]),
            threshold=float(meta["threshold"]),
            alarm_consecutive=int(meta.get("alarm_consecutive", 3)),
            weights=weights,
            layers=int(meta["config"]["layers"]),
        )

    def normalize(self, x: np.ndarray) -> np.ndarray:
        """Raw [..., window, features] → z-scores; gaps become 0 (= train mean), as in training."""
        return np.nan_to_num((x - self.mean) / self.std, nan=0.0).astype(np.float32)

    def logits(self, z: np.ndarray) -> np.ndarray:
        """z: normalized [batch, window, features] → logits [batch]."""
        w = self.weights
        h_seq = z
        for layer in range(self.layers):
            w_ih, w_hh = w[f"lstm.weight_ih_l{layer}"], w[f"lstm.weight_hh_l{layer}"]
            b = w[f"lstm.bias_ih_l{layer}"] + w[f"lstm.bias_hh_l{layer}"]
            hidden = w_hh.shape[1]
            h = np.zeros((z.shape[0], hidden), np.float32)
            c = np.zeros_like(h)
            x_proj = h_seq @ w_ih.T + b  # input projection for all steps at once
            outs = []
            for t in range(z.shape[1]):
                gates = x_proj[:, t] + h @ w_hh.T
                i, f, g, o = np.split(gates, 4, axis=1)
                c = _sigmoid(f) * c + _sigmoid(i) * np.tanh(g)
                h = _sigmoid(o) * np.tanh(c)
                outs.append(h)
            h_seq = np.stack(outs, axis=1)
        hid = np.maximum(h @ w["head.0.weight"].T + w["head.0.bias"], 0.0)
        return (hid @ w["head.3.weight"].T + w["head.3.bias"])[:, 0]

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Raw window(s) [window, features] or [batch, window, features] → P(degradation within horizon)."""
        batch = x[None] if x.ndim == 2 else x
        return _sigmoid(self.logits(self.normalize(batch)))

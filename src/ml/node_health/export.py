"""Convert the notebook artifact (`node_health_lstm.pt`) into a torch-free model directory.

    python -m src.ml.node_health.export --pt dataset/telemetry_sim/models/node_health_lstm.pt \
        --out models/node_health/v1 --version lstm-v1

Needs torch (training side only). Verifies the numpy forward pass against torch before writing.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from src.ml.node_health.model import META_FILE, WEIGHTS_FILE, HealthModel


def export(pt_path: Path, out: Path, version: str) -> Path:
    import torch
    from torch import nn

    art = torch.load(pt_path, map_location="cpu", weights_only=False)
    cfg = art["config"]
    out.mkdir(parents=True, exist_ok=True)
    np.savez(out / WEIGHTS_FILE, **{k: v.numpy() for k, v in art["state_dict"].items()})
    meta = {k: art[k] for k in ("features", "mean", "std", "counters_as_delta", "window", "horizon", "sample_sec",
                                 "threshold", "alarm_consecutive", "config", "test")}
    (out / META_FILE).write_text(json.dumps({"version": version, **meta}, indent=2), encoding="utf-8")

    # parity check: rebuild the torch module and compare on random windows
    class _Ref(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(len(meta["features"]), cfg["hidden"], cfg["layers"], batch_first=True)
            self.head = nn.Sequential(nn.Linear(cfg["hidden"], 32), nn.ReLU(), nn.Dropout(0), nn.Linear(32, 1))

        def forward(self, x):
            return self.head(self.lstm(x)[1][0][-1]).squeeze(-1)

    ref = _Ref()
    ref.load_state_dict(art["state_dict"])
    ref.eval()
    z = np.random.default_rng(0).normal(size=(16, meta["window"], len(meta["features"]))).astype(np.float32)
    with torch.no_grad():
        expected = ref(torch.from_numpy(z)).numpy()
    got = HealthModel.load(out).logits(z)
    err = float(np.abs(expected - got).max())
    if err > 1e-4:
        raise RuntimeError(f"numpy/torch mismatch: max |Δlogit| = {err}")
    print(f"exported {version} -> {out}  (parity max |dlogit| = {err:.2e})")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pt", type=Path, default=Path("dataset/telemetry_sim/models/node_health_lstm.pt"))
    ap.add_argument("--out", type=Path, default=Path("models/node_health/lstm-v1"))
    ap.add_argument("--version", default="lstm-v1")
    a = ap.parse_args()
    export(a.pt, a.out, a.version)

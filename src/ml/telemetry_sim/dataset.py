"""Sliding windows for a sequence model (LSTM): X[t-W+1..t] → will the node degrade within `horizon`?

Split is by node so validation/test measure generalisation to unseen nodes; normalisation stats come from
the train split only. Status enums are excluded from inputs (spec §23.3: they encode the failure itself).
"""

import csv
import gzip
from pathlib import Path

import numpy as np

from src.ml.telemetry_sim.labels import STATES, future_targets

# MVP node-health tree: Connectivity / Hardware / Runtime
FEATURES = [
    "heartbeat_age_sec", "connection_reconnect_count",  # connectivity (reconnects = connection errors)
    "cpu_usage_pct", "memory_usage_pct", "gpu_usage_pct", "gpu_temperature_c", "disk_usage_pct",  # hardware
    "inference_fps", "inference_latency_ms", "runtime_restart_count", "runtime_error_count",  # runtime
]
COUNTERS = ["connection_reconnect_count", "runtime_restart_count"]  # cumulative → per-step delta in build
_STATE_INDEX = {s.value: i for i, s in enumerate(STATES)}


def _load(path: Path, features: list[str]) -> tuple[np.ndarray, np.ndarray, str, str]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    x = np.array([[float(r[k]) if r[k] != "" else np.nan for k in features] for r in rows], dtype=np.float32)
    state = np.array([_STATE_INDEX[r["state"]] for r in rows], dtype=np.int8)
    return x, state, rows[0]["node_id"], rows[0]["scenario"]


def _ffill(x: np.ndarray) -> np.ndarray:
    """Carry the last reading forward (what a live window would hold); leading gaps stay NaN."""
    idx = np.where(~np.isnan(x), np.arange(len(x))[:, None], 0)
    np.maximum.accumulate(idx, axis=0, out=idx)
    out = x[idx, np.arange(x.shape[1])]
    out[np.isnan(x) & (idx == 0) & np.isnan(x[0])] = np.nan
    return out


def episode_matrix(path: Path, features: list[str] = FEATURES) -> tuple[np.ndarray, np.ndarray, str, str]:
    """Model-ready (unscaled) inputs of one episode: forward-filled, counters as per-step deltas."""
    x, state, node_id, scenario = _load(path, features)
    x = _ffill(x)
    for k in COUNTERS:
        if k in features:
            j = features.index(k)
            x[:, j] = np.clip(np.diff(x[:, j], prepend=x[0, j]), 0, None)
    return x, state, node_id, scenario


def build(src: Path, out: Path, window: int = 60, horizon: int = 120, stride: int = 6,
          pre_failure_only: bool = True, split: tuple[float, float] = (0.7, 0.15), seed: int = 0,
          features: list[str] = FEATURES) -> dict[str, int]:
    files = sorted((src / "episodes").glob("*.csv.gz"))
    nodes = sorted({f.name.rsplit("-e", 1)[0] for f in files})
    rng = np.random.default_rng(seed)
    rng.shuffle(nodes)
    n_tr, n_va = int(len(nodes) * split[0]), int(len(nodes) * split[1])
    part_of = {n: "train" if i < n_tr else "val" if i < n_tr + n_va else "test" for i, n in enumerate(nodes)}

    scenarios: list[str] = []
    buckets: dict[str, dict[str, list]] = {p: {"X": [], "y": [], "state": [], "ttd": [], "scenario": []}
                                            for p in ("train", "val", "test")}
    for f in files:
        x, state, node_id, scenario = episode_matrix(f, features)
        y, nxt, censored = future_targets(state, horizon)
        if scenario not in scenarios:
            scenarios.append(scenario)
        b = buckets[part_of[node_id]]
        for t in range(window - 1, len(x), stride):
            if censored[t] or (pre_failure_only and state[t] >= 2):
                continue
            b["X"].append(x[t - window + 1: t + 1])
            b["y"].append(y[t])
            b["state"].append(state[t])
            b["ttd"].append(nxt[t] * 5.0 if nxt[t] > 0 else -1.0)
            b["scenario"].append(scenarios.index(scenario))

    arrays: dict[str, np.ndarray] = {}
    for p, b in buckets.items():
        arrays[f"X_{p}"] = np.stack(b["X"]).astype(np.float32) if b["X"] else np.zeros((0, window, len(features)), np.float32)
        for k in ("y", "state", "ttd", "scenario"):
            arrays[f"{k}_{p}"] = np.asarray(b[k])
    flat = arrays["X_train"].reshape(-1, len(features))
    mean, std = np.nanmean(flat, axis=0), np.nanstd(flat, axis=0) + 1e-6
    for p in buckets:
        z = (arrays[f"X_{p}"] - mean) / std
        arrays[f"X_{p}"] = np.nan_to_num(z, nan=0.0).astype(np.float32)  # NaN → train mean

    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, **arrays, feature_names=np.array(features), mean=mean, std=std,
                        scenario_names=np.array(scenarios), state_names=np.array([s.value for s in STATES]),
                        window=window, horizon=horizon, stride=stride,
                        **{f"nodes_{p}": np.array(sorted(n for n, q in part_of.items() if q == p)) for p in buckets})
    return {p: len(buckets[p]["y"]) for p in buckets} | {
        f"pos_{p}": int(np.sum(buckets[p]["y"])) for p in buckets}

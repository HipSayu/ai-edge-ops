"""Operational state (spec §17) derived from observables, and the early-warning target (spec §18).

States come from what an operator would see, not from the injected severity, so a fault that the node
absorbs never becomes a positive and a benign burst that genuinely drops FPS does.
"""

import numpy as np

from src.shared.contracts import OperationalState, RuntimeStatus

STATES = [OperationalState.NORMAL, OperationalState.WARNING, OperationalState.DEGRADED, OperationalState.CRITICAL]
DEBOUNCE = 3  # consecutive samples (15 s) a condition must hold


def _nan(rows: list[dict], key: str) -> np.ndarray:
    return np.array([np.nan if r.get(key) is None else float(r[key]) for r in rows])


def _held(cond: np.ndarray, k: int = DEBOUNCE) -> np.ndarray:
    run, out = 0, np.zeros_like(cond)
    for i, c in enumerate(cond):
        run = run + 1 if c else 0
        out[i] = run >= k
    return out


def operational_states(rows: list[dict], throttle_temp_c: float, baseline_steps: int = 120) -> np.ndarray:
    """Per-row state index into STATES. Baseline FPS/latency = median over the (healthy) first `baseline_steps`."""
    with np.errstate(invalid="ignore"):
        g = lambda k: _nan(rows, k)  # noqa: E731
        lat = g("inference_latency_ms")
        base_lat = np.nanmedian(lat[:baseline_steps])
        fps = g("inference_fps")
        base_fps = np.nanmedian(fps[:baseline_steps])
        hb, err, disk = g("heartbeat_age_sec"), g("runtime_error_rate"), g("disk_usage_pct")
        failed = np.array([r.get("runtime_status") in (RuntimeStatus.FAILED, RuntimeStatus.RESTARTING) for r in rows])

        critical = (hb > 30) | failed | (fps < 0.2 * base_fps) | (disk >= 99)
        degraded = (hb > 15) | (fps < 0.7 * base_fps) | (lat > 2 * base_lat) | (err > 5)
        warning = (
            (hb > 10) | (g("cpu_usage_pct") > 85) | (g("memory_usage_pct") > 88) | (g("gpu_usage_pct") > 95)
            | (g("gpu_temperature_c") > throttle_temp_c - 5) | (disk > 90)
            | (fps < 0.9 * base_fps) | (lat > 1.4 * base_lat) | (err > 1.5)
        )
    state = np.zeros(len(rows), dtype=np.int8)
    state[_held(warning)] = 1
    state[_held(degraded)] = 2
    state[_held(critical, 1)] = 3  # hard failures count immediately
    return state


def future_targets(state: np.ndarray, horizon: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """For each t: y = DEGRADED/CRITICAL within (t, t+horizon]; steps until it (-1 = none);
    censored = window runs past the episode end without an event (label unknowable)."""
    bad = state >= 2
    n = len(state)
    nxt = np.full(n, -1, dtype=np.int64)
    upcoming = -1
    for i in range(n - 1, -1, -1):
        nxt[i] = upcoming - i if upcoming >= 0 else -1
        if bad[i]:
            upcoming = i
    y = ((nxt > 0) & (nxt <= horizon)).astype(np.int8)
    censored = (y == 0) & (np.arange(n) + horizon >= n)
    return y, nxt, censored

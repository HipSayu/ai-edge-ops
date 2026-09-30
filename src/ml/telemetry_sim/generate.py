"""Episode generation: warm-up (healthy) → fault ramp → hold → optional recovery, written as CSV.gz."""

import csv
import gzip
import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from src.ml.telemetry_sim.dataset import FEATURES
from src.ml.telemetry_sim.labels import STATES, future_targets, operational_states
from src.ml.telemetry_sim.profiles import NodeSpec, make_fleet
from src.ml.telemetry_sim.scenarios import BENIGN, FAILURES, SCENARIOS, Faults, severity
from src.ml.telemetry_sim.simulator import DT, GPU_COLUMNS, STATUS_COLUMNS, TELEMETRY_COLUMNS, NodeModel

META_COLUMNS = ["timestamp", "cluster_id", "node_id", "runtime_id", "episode_id", "scenario", "phase", "fault_severity", "state", "future_degradation", "time_to_degradation_sec"]
HORIZON = 120  # steps (10 min) for the CSV future_degradation column (spec §18)
_MIN = 60 / DT  # steps per minute


def _steps(rng: np.random.Generator, lo_hi: tuple[float, float]) -> int:
    return max(1, int(rng.uniform(*lo_hi) * _MIN))


def simulate_episode(spec: NodeSpec, scenario: str, rng: np.random.Generator,
                     recover_prob: float = 0.4) -> tuple[list[dict], list[dict]]:
    """Returns (telemetry rows, meta rows). `scenario == 'healthy'` never injects a fault."""
    node = NodeModel(spec, rng)
    warmup = _steps(rng, (30, 90))
    if scenario == "healthy":
        plan = [("healthy", warmup + _steps(rng, (30, 120)))]
        sc = None
    else:
        sc = SCENARIOS[scenario]
        ramp, hold = _steps(rng, sc.ramp_min), _steps(rng, sc.hold_min)
        plan = [("healthy", warmup), ("ramp", ramp), ("hold", hold)]
        if not sc.failure or rng.random() < recover_prob:
            plan.append(("recovery", _steps(rng, (10, 40))))

    rows, meta = [], []
    phase_offset = float(rng.uniform(0, 2 * np.pi))
    t = 0
    for phase, length in plan:
        if phase == "recovery":
            node.restart_runtime()
        for k in range(length):
            f, s = Faults(), 0.0
            if sc is not None and phase in ("ramp", "hold"):
                progress = k / plan[1][1] if phase == "ramp" else 1.0
                s = severity(sc.shape, progress, t * DT, phase_offset)
                sc.apply(f, s, rng)
            rows.append(node.step(f))
            meta.append({"phase": phase, "fault_severity": round(s, 4)})
            t += 1
    return rows, meta


def _drop_samples(rows: list[dict], rng: np.random.Generator, p_row: float = 0.004, p_gpu: float = 0.01) -> None:
    """Collector hiccups: occasional missing metric, occasional missing GPU message."""
    for r in rows:
        if len(r) < 3:
            continue
        if rng.random() < p_gpu:
            for k in GPU_COLUMNS:
                r[k] = None
        for k in TELEMETRY_COLUMNS:
            if k not in STATUS_COLUMNS and rng.random() < p_row:
                r[k] = None


def _fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return f"{v:.4g}" if abs(v) < 1e5 else f"{v:.0f}"
    return str(v)


def generate(out: Path, n_nodes: int, episodes_per_node: int, seed: int,
             failure_ratio: float = 0.65, benign_ratio: float = 0.15) -> Path:
    rng = np.random.default_rng(seed)
    out.mkdir(parents=True, exist_ok=True)
    (out / "episodes").mkdir(exist_ok=True)
    fleet = make_fleet(n_nodes, rng)
    (out / "fleet.json").write_text(json.dumps(
        [{**asdict(s), "profile": s.profile.name} for s in fleet], indent=2), encoding="utf-8")

    manifest = []
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for spec in fleet:
        clock = start + timedelta(hours=float(rng.uniform(0, 24)))
        for e in range(episodes_per_node):
            u = rng.random()
            scenario = (str(rng.choice(FAILURES)) if u < failure_ratio
                        else str(rng.choice(BENIGN)) if u < failure_ratio + benign_ratio else "healthy")
            rows, meta = simulate_episode(spec, scenario, rng)
            states = operational_states(rows, spec.profile.throttle_temp_c)
            future, nxt, _ = future_targets(states, HORIZON)
            _drop_samples(rows, rng)

            episode_id = f"{spec.node_id}-e{e:03d}"
            path = out / "episodes" / f"{episode_id}.csv.gz"
            with gzip.open(path, "wt", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(META_COLUMNS + FEATURES)
                for i, (r, m) in enumerate(zip(rows, meta)):
                    ts = (clock + timedelta(seconds=i * DT)).isoformat()
                    w.writerow([ts, spec.cluster_id, spec.node_id, f"{spec.node_id}-rt0", episode_id, scenario, m["phase"],
                                m["fault_severity"], STATES[states[i]].value, int(future[i]),
                                nxt[i] * DT if nxt[i] > 0 else ""]
                               + [_fmt(r.get(k)) for k in FEATURES])
            bad = np.flatnonzero(states >= 2)
            onset = next((i for i, m in enumerate(meta) if m["phase"] == "ramp"), -1)
            manifest.append({
                "episode_id": episode_id, "cluster_id": spec.cluster_id, "node_id": spec.node_id, "profile": spec.profile.name,
                "scenario": scenario, "steps": len(rows), "fault_onset_step": onset,
                "first_degraded_step": int(bad[0]) if len(bad) else -1,
                "lead_time_sec": (int(bad[0]) - onset) * DT if len(bad) and onset >= 0 else "",
                "throttle_temp_c": spec.profile.throttle_temp_c,
            })
            clock += timedelta(seconds=len(rows) * DT + float(rng.uniform(600, 7200)))

    with open(out / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(manifest[0]))
        w.writeheader()
        w.writerows(manifest)
    return out / "manifest.csv"

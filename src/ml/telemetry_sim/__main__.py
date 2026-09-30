"""python -m src.ml.telemetry_sim {generate,build} ... (see --help)."""

import argparse
import json
from pathlib import Path

from src.ml.telemetry_sim.dataset import build
from src.ml.telemetry_sim.generate import generate


def main() -> None:
    ap = argparse.ArgumentParser(prog="telemetry_sim")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="simulate node episodes to <out>/episodes/*.csv.gz + manifest.csv")
    g.add_argument("--out", type=Path, default=Path("data/telemetry_sim"))
    g.add_argument("--nodes", type=int, default=40)
    g.add_argument("--episodes-per-node", type=int, default=10)
    g.add_argument("--failure-ratio", type=float, default=0.65)
    g.add_argument("--benign-ratio", type=float, default=0.15)
    g.add_argument("--seed", type=int, default=0)
    b = sub.add_parser("build", help="sliding windows → .npz for LSTM training")
    b.add_argument("--src", type=Path, default=Path("data/telemetry_sim"))
    b.add_argument("--out", type=Path, default=Path("data/telemetry_sim/lstm_w60_h120.npz"))
    b.add_argument("--window", type=int, default=60, help="input steps (60 × 5 s = 5 min)")
    b.add_argument("--horizon", type=int, default=120, help="prediction steps (120 × 5 s = 10 min)")
    b.add_argument("--stride", type=int, default=6)
    b.add_argument("--include-degraded", action="store_true", help="keep windows already in DEGRADED/CRITICAL")
    b.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    if a.cmd == "generate":
        print(generate(a.out, a.nodes, a.episodes_per_node, a.seed, a.failure_ratio, a.benign_ratio))
    else:
        stats = build(a.src, a.out, a.window, a.horizon, a.stride, not a.include_degraded, seed=a.seed)
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

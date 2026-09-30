"""Failure scenarios (spec §21) as latent fault drivers.

A scenario never writes telemetry directly: it maps a severity s ∈ [0, 1] to latent `Faults`, and the
node model in `simulator.py` turns those into observables (so e.g. a thermal fault shows up as throttling →
lower clock → higher latency → lower FPS, exactly the causal chain the model has to learn).
"""

from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass(slots=True)
class Faults:
    cpu_extra_pct: float = 0.0  # foreign CPU load
    mem_leak_mb: float = 0.0
    gpu_extra_pct: float = 0.0  # co-located GPU work
    gpu_mem_extra_mb: float = 0.0
    cooling_loss: float = 0.0  # 0 = nominal, 1 = fan dead
    power_cap: float = 1.0  # fraction of power budget available
    disk_extra_pct: float = 0.0
    disk_io_extra: float = 0.0  # extra MB/s written
    rtt_extra_ms: float = 0.0
    loss_extra_pct: float = 0.0
    camera_fps_factor: float = 1.0
    camera_blur: float = 0.0
    camera_freeze: bool = False
    camera_disconnect: bool = False
    worker_slowdown: float = 1.0
    worker_error_pct: float = 0.0
    worker_crash: bool = False
    drift: float = 0.0
    process_extra: int = 0
    node_hang: bool = False
    activity_boost: float = 0.0  # benign: busier scene


Apply = Callable[[Faults, float, np.random.Generator], None]


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    ramp_min: tuple[float, float]  # minutes from onset to full severity
    shape: str  # linear | accelerating | sudden | flapping
    apply: Apply
    failure: bool = True  # False = hard negative (must not raise the alarm)
    hold_min: tuple[float, float] = (5, 20)
    tags: dict = field(default_factory=dict)


def _cpu_pressure(f: Faults, s: float, rng: np.random.Generator) -> None:
    f.cpu_extra_pct = 90 * s
    f.process_extra = int(40 * s)


def _memory_leak(f: Faults, s: float, rng: np.random.Generator) -> None:
    f.mem_leak_mb = s  # scaled by node memory in the simulator (fraction of free RAM + overshoot)
    f.worker_crash = s >= 1.0  # OOM kill


def _gpu_overload(f: Faults, s: float, rng: np.random.Generator) -> None:
    f.gpu_extra_pct = 85 * s
    f.gpu_mem_extra_mb = s  # fraction of free GPU memory


def _thermal(f: Faults, s: float, rng: np.random.Generator) -> None:
    f.cooling_loss = 1.6 * s


def _disk(f: Faults, s: float, rng: np.random.Generator) -> None:
    f.disk_extra_pct = s  # fraction of remaining space consumed
    f.disk_io_extra = 40 * s


def _network(f: Faults, s: float, rng: np.random.Generator) -> None:
    f.rtt_extra_ms = 600 * s**2
    f.loss_extra_pct = 30 * s**1.5


def _worker(f: Faults, s: float, rng: np.random.Generator) -> None:
    f.worker_slowdown = 1.0 + 2.5 * s**2
    f.worker_error_pct = 25 * s**2
    f.worker_crash = s >= 1.0


def _node(f: Faults, s: float, rng: np.random.Generator) -> None:
    f.cpu_extra_pct = 70 * s
    f.mem_leak_mb = 2.0 * s  # sudden shape caps precursor s at 0.45 → ~90 % of free RAM
    f.disk_io_extra = 15 * s
    f.process_extra = int(150 * s)
    f.node_hang = s >= 1.0


def _load_burst(f: Faults, s: float, rng: np.random.Generator) -> None:
    f.activity_boost = 0.6 * s


def _network_blip(f: Faults, s: float, rng: np.random.Generator) -> None:
    f.rtt_extra_ms = 120 * s
    f.loss_extra_pct = 3 * s


SCENARIOS: dict[str, Scenario] = {
    s.name: s
    for s in (
        Scenario("cpu_pressure", (10, 40), "linear", _cpu_pressure),
        Scenario("memory_leak", (30, 120), "linear", _memory_leak, hold_min=(1, 3)),
        Scenario("gpu_overload", (5, 30), "linear", _gpu_overload),
        Scenario("thermal_throttling", (15, 60), "accelerating", _thermal),
        Scenario("disk_pressure", (30, 150), "accelerating", _disk),
        Scenario("network_degradation", (10, 40), "flapping", _network),
        Scenario("inference_worker_failure", (5, 25), "accelerating", _worker, hold_min=(2, 8)),
        Scenario("node_failure", (10, 30), "sudden", _node, hold_min=(3, 10)),
        # hard negatives: look alarming for a moment, never degrade
        Scenario("load_burst", (1, 5), "flapping", _load_burst, failure=False, hold_min=(2, 15)),
        Scenario("network_blip", (0.5, 2), "flapping", _network_blip, failure=False, hold_min=(0.5, 3)),
    )
}
FAILURES = [n for n, s in SCENARIOS.items() if s.failure]
BENIGN = [n for n, s in SCENARIOS.items() if not s.failure]


def severity(shape: str, progress: float, t_sec: float, phase: float) -> float:
    """Severity at `progress` ∈ [0, 1] of the ramp; ≥ 1 after the ramp completes."""
    p = min(max(progress, 0.0), 1.0)
    if progress >= 1.0:
        return 1.0
    if shape == "accelerating":
        return p**2.5
    if shape == "sudden":  # mild precursor, then a jump at the end of the ramp
        return 0.45 * p
    if shape == "flapping":  # bursts whose envelope grows
        on = np.sin(2 * np.pi * t_sec / 240.0 + phase) > -0.2
        return p * (1.0 if on else 0.3)
    return p

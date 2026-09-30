"""Device profiles and per-node variation. Numbers are rough public figures, not measurements."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    name: str
    gpu_name: str
    cpu_cores: int
    memory_total_mb: float
    gpu_memory_mb: float  # == memory_total_mb on unified-memory Jetsons
    disk_total_gb: float
    idle_power_w: float
    max_power_w: float
    power_limit_w: float
    gpu_freq_max_mhz: float
    throttle_temp_c: float
    thermal_resistance: float  # °C per W at nominal cooling
    base_latency_ms: float  # one frame at full clock, idle scene
    target_fps: float


PROFILES: dict[str, DeviceProfile] = {
    p.name: p
    for p in (
        DeviceProfile("jetson_orin_nano", "Orin Nano", 6, 7_600, 7_600, 128, 5.0, 15.0, 15.0, 625, 90.0, 2.6, 34.0, 15),
        DeviceProfile("jetson_orin_nx", "Orin NX", 8, 15_600, 15_600, 256, 7.0, 25.0, 25.0, 918, 90.0, 1.6, 22.0, 25),
        DeviceProfile("x86_rtx3060", "RTX 3060", 12, 32_000, 12_000, 512, 45.0, 260.0, 260.0, 1_780, 83.0, 0.17, 9.0, 30),
    )
}


@dataclass(frozen=True, slots=True)
class NodeSpec:
    """A concrete node: profile + site-specific variation that stays fixed across its episodes."""

    cluster_id: str
    node_id: str
    profile: DeviceProfile
    ambient_c: float
    cooling: float  # multiplier on thermal resistance (dusty enclosure > 1)
    latency_ms: float
    camera_fps: float
    target_fps: float
    base_rtt_ms: float
    base_disk_pct: float
    base_memory_mb: float
    activity_level: float  # typical scene busyness 0..1


def make_fleet(n_nodes: int, rng: np.random.Generator, n_clusters: int = 4) -> list[NodeSpec]:
    names = list(PROFILES)
    weights = np.array([0.45, 0.35, 0.20])
    fleet = []
    for i in range(n_nodes):
        p = PROFILES[names[rng.choice(len(names), p=weights)]]
        camera_fps = float(rng.choice([15, 25, 30]))
        fleet.append(NodeSpec(
            cluster_id=f"sim-cluster-{i * n_clusters // n_nodes}",
            node_id=f"sim-node-{i:03d}",
            profile=p,
            ambient_c=float(rng.uniform(22, 38)),
            cooling=float(rng.uniform(0.85, 1.2)),
            latency_ms=p.base_latency_ms * float(rng.uniform(0.85, 1.2)),
            camera_fps=camera_fps,
            target_fps=min(camera_fps, p.target_fps),
            base_rtt_ms=float(rng.uniform(8, 60)),
            base_disk_pct=float(rng.uniform(25, 70)),
            base_memory_mb=p.memory_total_mb * float(rng.uniform(0.30, 0.50)),
            activity_level=float(rng.uniform(0.2, 0.7)),
        ))
    return fleet

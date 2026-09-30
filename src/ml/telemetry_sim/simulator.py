"""Node model: latent faults + scene activity → one telemetry sample per 5 s step.

Observables are coupled through a small causal pipeline (thermal/power → clock → latency → capacity →
FPS/queue → frame age; swap/foreign load → contention → latency; ...) so failure signatures emerge from the
dynamics instead of being painted onto individual columns.
"""

import math
from dataclasses import dataclass

import numpy as np

from src.ml.telemetry_sim.profiles import NodeSpec
from src.ml.telemetry_sim.scenarios import Faults
from src.shared.contracts import CameraStatus, GpuTelemetry, NodeStatus, RuntimeStatus, RuntimeTelemetry, SystemTelemetry

DT = 5.0  # seconds per sample (spec §15)
QUEUE_MAX = 64

_SKIP = {"timestamp", "node_id", "runtime_id"}
TELEMETRY_COLUMNS = [
    *(k for k in SystemTelemetry.model_fields if k not in _SKIP),
    *(k for k in GpuTelemetry.model_fields if k not in _SKIP),
    *(k for k in RuntimeTelemetry.model_fields if k not in _SKIP),
    "heartbeat_age_sec",  # computed Cloud-side from NodeState arrival (spec §14)
]
GPU_COLUMNS = [k for k in GpuTelemetry.model_fields if k not in _SKIP]
STATUS_COLUMNS = {"agent_status", "runtime_status", "camera_status", "thermal_throttling", "power_throttling"}


def _ema(prev: float, value: float, horizon_sec: float) -> float:
    a = min(1.0, DT / horizon_sec)
    return prev + a * (value - prev)


@dataclass(slots=True)
class _Rates:
    mem: float = 0.0
    temp: float = 0.0
    power: float = 0.0
    output_change: float = 0.0


class NodeModel:
    def __init__(self, spec: NodeSpec, rng: np.random.Generator) -> None:
        p = spec.profile
        self.spec = spec
        self.rng = rng
        self.activity = spec.activity_level
        self.runtime_mem_mb = min(p.memory_total_mb * 0.18, 2_600.0)
        self.model_gpu_mem_mb = min(p.gpu_memory_mb * 0.22, 2_200.0)
        self.temp = spec.ambient_c + p.idle_power_w * p.thermal_resistance * spec.cooling * 1.8
        self.power = p.idle_power_w * 1.8
        self.queue = 0.0
        self.disk_pct = spec.base_disk_pct
        self.cpu_load_1m = self.cpu_load_5m = p.cpu_cores * 0.3
        self.last_mem = spec.base_memory_mb + self.runtime_mem_mb
        self.last_detections = 0
        self.rates = _Rates()
        self.uptime = float(rng.uniform(3_600, 30 * 86_400))
        self.runtime_uptime = float(rng.uniform(600, self.uptime))
        self.reboot_count = int(rng.integers(0, 6))
        self.restart_count = int(rng.integers(0, 3))
        self.reconnects = int(rng.integers(0, 5))
        self.telemetry_queue = 0.0
        self.freeze_sec = 0.0
        self.down_sec = 0.0  # >0 while the runtime process is dead / restarting
        self.hang_sec = 0.0
        self.heartbeat_age = 0.0

    def restart_runtime(self) -> None:
        """Operator/auto remediation at recovery: fresh process, empty queue, leak cleared."""
        self.restart_count += 1
        self.runtime_uptime = 0.0
        self.queue = 0.0
        self.down_sec = 0.0
        self.hang_sec = 0.0
        self.heartbeat_age = 0.0

    def step(self, f: Faults) -> dict[str, float | str | bool | None]:
        s, p, rng = self.spec, self.spec.profile, self.rng
        n = rng.normal

        if f.node_hang:  # agent/node unresponsive: nothing arrives, heartbeat ages
            self.hang_sec += DT
            self.heartbeat_age += DT
            return {"heartbeat_age_sec": self.heartbeat_age, "agent_status": NodeStatus.OFFLINE}
        self.uptime += DT
        self.runtime_uptime += DT

        # scene activity: mean-reverting random walk plus benign bursts
        self.activity = float(np.clip(self.activity + 0.02 * (s.activity_level - self.activity) + 0.03 * n(), 0, 1))
        act = min(1.2, self.activity + f.activity_boost)

        # camera
        if f.camera_disconnect:
            cam_fps, cam_status = 0.0, CameraStatus.DISCONNECTED
            self.freeze_sec = 0.0
        elif f.camera_freeze:
            self.freeze_sec += DT
            cam_fps, cam_status = 0.0, CameraStatus.FROZEN
        else:
            self.freeze_sec = 0.0
            cam_fps = max(0.0, s.camera_fps * f.camera_fps_factor * (1 + 0.01 * n()))
            cam_status = CameraStatus.DEGRADED if f.camera_fps_factor < 0.8 else CameraStatus.ONLINE
        cam_drop = float(np.clip((1 - f.camera_fps_factor) * 55 + abs(n(0, 0.3)), 0, 100))

        # memory (unified on Jetson: co-located GPU memory is also host memory)
        total = p.memory_total_mb
        free_for_leak = total - s.base_memory_mb - self.runtime_mem_mb
        leak = f.mem_leak_mb * free_for_leak * 1.08
        gpu_extra_mem = f.gpu_mem_extra_mb * max(0.0, p.gpu_memory_mb - self.model_gpu_mem_mb) * 0.97
        unified = p.gpu_memory_mb == p.memory_total_mb
        used = s.base_memory_mb + self.runtime_mem_mb + leak + (gpu_extra_mem if unified else 0) + n(0, 25)
        swap_pct = float(np.clip((used - 0.93 * total) / (0.25 * total) * 100, 0, 100))
        resident = min(used, 0.985 * total)
        self.rates.mem = _ema(self.rates.mem, (used - self.last_mem) / DT * 60, 120)
        self.last_mem = used

        # clocks: thermal throttling and power capping
        throttled = self.temp >= p.throttle_temp_c
        thermal_factor = max(0.35, 1 - (self.temp - p.throttle_temp_c) * 0.06) if throttled else 1.0
        freq_factor = min(thermal_factor, f.power_cap**0.8)

        # inference pipeline
        contention = f.cpu_extra_pct / 100 * 1.2 + swap_pct / 100 * 2.5 + f.gpu_extra_pct / 100 * 1.1
        frame_ms = s.latency_ms * (1 + 0.35 * act) / freq_factor
        latency = frame_ms * f.worker_slowdown * (1 + contention) * float(rng.lognormal(0, 0.04))
        capacity = 1000.0 / latency
        demand = min(cam_fps, s.target_fps)

        if f.worker_crash or used > 1.02 * total:  # crash-loop: dies, restarts ~every minute
            if self.down_sec <= 0:
                self.restart_count += 1
                self.runtime_uptime = 0.0
            self.down_sec = self.down_sec + DT if self.down_sec < 60 else 0.0
        else:
            self.down_sec = 0.0
        down = self.down_sec > 0

        disk_err = max(0.0, self.disk_pct - 97) * 8
        err = float(np.clip(0.2 + f.worker_error_pct + disk_err + abs(n(0, 0.1)), 0, 100))
        served = 0.0 if down else min(demand, capacity)
        if down:
            self.queue = 0.0
        else:
            self.queue = float(np.clip(self.queue + (demand - capacity) * DT, 0, QUEUE_MAX))
        if self.queue >= QUEUE_MAX and demand > capacity:
            cam_drop = min(100.0, cam_drop + (demand - capacity) / demand * 100)
        fps = served * (1 - err / 100) * (1 + 0.01 * n())
        budget_ms = 1000.0 / s.target_fps
        timeout = float(np.clip((latency / (3 * budget_ms) - 1) * 50, 0, 100))
        spread = 1.25 + 0.3 * act + 0.4 * contention

        # GPU / CPU
        busy = served * frame_ms / 1000 + f.gpu_extra_pct / 100
        gpu = float(np.clip(100 * busy + n(0, 2), 0, 100))
        gpu_freq = p.gpu_freq_max_mhz * freq_factor * (0.55 + 0.45 * min(1.0, busy))
        runtime_cpu = 0.0 if down else 6 + 30 * act * served / s.target_fps + n(0, 1.5)
        cpu = float(np.clip(8 + runtime_cpu + f.cpu_extra_pct + swap_pct * 0.2 + n(0, 2), 0, 100))
        iowait = float(np.clip(1 + f.disk_io_extra * 0.4 + swap_pct * 0.3 + abs(n(0, 0.4)), 0, 100))
        self.cpu_load_1m = _ema(self.cpu_load_1m, cpu / 100 * p.cpu_cores * (1 + iowait / 50), 60)
        self.cpu_load_5m = _ema(self.cpu_load_5m, self.cpu_load_1m, 300)

        # power & thermal (first-order plant; throttling emerges when cooling degrades)
        raw_power = p.idle_power_w + (p.max_power_w - p.idle_power_w) * (0.65 * gpu / 100 + 0.35 * cpu / 100)
        power = min(raw_power, p.power_limit_w * f.power_cap) * (1 + 0.02 * n())
        self.rates.power = _ema(self.rates.power, (power - self.power) / DT * 60, 60)
        self.power = power
        r_th = p.thermal_resistance * s.cooling * (1 + 1.2 * f.cooling_loss)
        t_eq = s.ambient_c + power * r_th
        new_temp = self.temp + (t_eq - self.temp) * DT / 150
        self.rates.temp = _ema(self.rates.temp, (new_temp - self.temp) / DT * 60, 60)
        self.temp = new_temp

        # storage
        self.disk_pct = min(99.9, self.disk_pct + 0.0004)
        disk = min(99.9, self.disk_pct + f.disk_extra_pct * (99.8 - self.disk_pct))
        write = max(0.0, 1.5 + f.disk_io_extra + n(0, 0.3))

        # network
        loss = float(np.clip(0.1 + f.loss_extra_pct * rng.uniform(0.6, 1.4) + abs(n(0, 0.05)), 0, 100))
        rtt = max(1.0, s.base_rtt_ms * (1 + 0.1 * n()) + f.rtt_extra_ms * rng.uniform(0.7, 1.3))
        if rng.random() < loss / 100 * 0.4:
            self.reconnects += 1
        self.telemetry_queue = float(np.clip(
            self.telemetry_queue + (3 if rng.random() < loss / 100 * 2 else -2) + (rtt > 800) * 2, 0, 500))
        # heartbeat (retained NodeState, QoS1 with 2 retries): lost or late under loss / high RTT
        if rng.random() < 1 - (loss / 100) ** 0.6 and rtt < 1_500:
            self.heartbeat_age = float(rng.uniform(0, DT)) + rtt / 1000
        else:
            self.heartbeat_age += DT

        # model output
        if served > 0:
            lam = (1 + 14 * act) * (1 - 0.5 * f.drift) * (1 - 0.4 * f.camera_blur)
            detections = int(rng.poisson(max(lam, 0.05)))
            conf_mean = float(np.clip(0.82 - 0.32 * f.drift - 0.25 * f.camera_blur + n(0, 0.015), 0.05, 0.99))
            conf_std = 0.08 + 0.08 * f.drift + abs(n(0, 0.01))
            conf_min = max(0.25, conf_mean - 2.5 * conf_std + n(0, 0.02))
            entropy = max(0.0, 0.6 + 0.3 * act + 0.7 * f.drift + n(0, 0.05))
            unknown = float(np.clip(1.5 + 25 * f.drift + n(0, 0.5), 0, 100))
            change = abs(detections - self.last_detections) / max(1, self.last_detections)
            self.rates.output_change = _ema(self.rates.output_change, change + 0.4 * f.drift, 60)
            self.last_detections = detections
        else:
            detections, conf_mean, conf_std, conf_min, entropy, unknown = 0, None, None, None, None, None

        ratio = fps / s.target_fps
        if down:
            runtime_status = RuntimeStatus.FAILED if self.down_sec < 45 else RuntimeStatus.RESTARTING
        elif ratio < 0.7 or err > 5:
            runtime_status = RuntimeStatus.DEGRADED
        else:
            runtime_status = RuntimeStatus.RUNNING
        agent = NodeStatus.DEGRADED if runtime_status in (RuntimeStatus.FAILED, RuntimeStatus.DEGRADED) else NodeStatus.ONLINE

        frame_age = 1000 / max(cam_fps, 0.5) / 2 + self.queue / max(capacity, 0.1) * 1000 + self.freeze_sec * 1000
        return {
            # system
            "cpu_usage_pct": cpu,
            "cpu_load_1m": self.cpu_load_1m,
            "cpu_load_5m": self.cpu_load_5m,
            "cpu_iowait_pct": iowait,
            "cpu_context_switches": max(0.0, 3_000 + 80 * cpu + 40 * f.process_extra + n(0, 150)),
            "memory_usage_pct": resident / total * 100,
            "memory_available_mb": total - resident,
            "memory_used_mb": resident,
            "swap_usage_pct": swap_pct,
            "memory_growth_rate": self.rates.mem,
            "temperature_c": self.temp,
            "cpu_temperature_c": self.temp - 2 + n(0, 0.3),
            "temperature_rate": self.rates.temp,
            "thermal_throttling": throttled,
            "power_w": power,
            "power_rate": self.rates.power,
            "power_limit_w": p.power_limit_w * f.power_cap,
            "power_throttling": f.power_cap < 0.95 and raw_power > p.power_limit_w * f.power_cap,
            "disk_usage_pct": disk,
            "disk_free_gb": p.disk_total_gb * (1 - disk / 100),
            "inode_usage_pct": min(100.0, disk * 0.55 + f.disk_extra_pct * 40),
            "disk_read_mb_s": max(0.0, 2 + n(0, 0.4)),
            "disk_write_mb_s": write,
            "disk_io_wait_pct": iowait * 0.8,
            "network_rtt_ms": rtt,
            "packet_loss_pct": loss,
            "network_rx_mb_s": max(0.0, 0.5 * cam_fps / 30 + n(0, 0.02)),
            "network_tx_mb_s": max(0.0, 0.05 + 0.002 * detections + n(0, 0.005)),
            "connection_reconnect_count": self.reconnects,
            "mqtt_publish_latency_ms": rtt * 1.1 + loss * 15 + abs(n(0, 2)),
            "telemetry_queue_size": int(self.telemetry_queue),
            "node_uptime_sec": self.uptime,
            "reboot_count": self.reboot_count,
            "process_count": int(180 + f.process_extra + n(0, 3)),
            "agent_status": agent,
            # gpu
            "gpu_usage_pct": gpu,
            "gpu_memory_usage_pct": min(100.0, (self.model_gpu_mem_mb + gpu_extra_mem) / p.gpu_memory_mb * 100),
            "gpu_memory_used_mb": self.model_gpu_mem_mb + gpu_extra_mem,
            "gpu_frequency_mhz": gpu_freq,
            "gpu_power_w": power * 0.55 * gpu / 100,
            "gpu_temperature_c": self.temp + 2 + n(0, 0.3),
            # runtime
            "runtime_cpu_pct": max(0.0, runtime_cpu),
            "runtime_memory_mb": 0.0 if down else self.runtime_mem_mb + leak,
            "runtime_restart_count": self.restart_count,
            "runtime_uptime_sec": self.runtime_uptime,
            "runtime_error_rate": err,
            "runtime_error_count": int(rng.poisson(demand * DT * err / 100)),  # failed frames this interval
            "runtime_queue_size": int(self.queue),
            "runtime_status": runtime_status,
            "inference_fps": max(0.0, fps),
            "target_fps": s.target_fps,
            "effective_fps_ratio": max(0.0, ratio),
            "inference_latency_ms": None if down else latency,
            "inference_p50_ms": None if down else latency * 0.95,
            "inference_p95_ms": None if down else latency * spread,
            "inference_p99_ms": None if down else latency * spread * 1.25,
            "inference_error_rate": err,
            "inference_timeout_rate": timeout,
            "camera_fps": cam_fps,
            "camera_target_fps": s.camera_fps,
            "camera_frame_age_ms": min(frame_age, 120_000.0),
            "camera_frame_drop_pct": cam_drop,
            "camera_freeze_duration_sec": self.freeze_sec,
            "camera_brightness": float(np.clip(0.5 + 0.08 * math.sin(self.uptime / 86_400 * 2 * math.pi) + n(0, 0.01), 0, 1)),
            "camera_blur_score": float(np.clip(0.8 - 0.6 * f.camera_blur + n(0, 0.02), 0, 1)),
            "camera_status": cam_status,
            "detection_count": detections,
            "confidence_mean": conf_mean,
            "confidence_std": conf_std,
            "confidence_min": conf_min,
            "class_entropy": entropy,
            "unknown_detection_rate": unknown,
            "output_change_rate": self.rates.output_change,
            "heartbeat_age_sec": self.heartbeat_age,
        }

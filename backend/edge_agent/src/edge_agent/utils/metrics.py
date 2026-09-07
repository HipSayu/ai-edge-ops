"""Edge host metrics helpers."""

from __future__ import annotations

import logging
import shutil
import subprocess

import edge_protocol as p
import psutil
from dqh.svc_core.helpers.time import utcnow

from edge_agent.core.hardware import Hardware

logger = logging.getLogger("edge_agent.metrics")


def _gpu_stats() -> tuple[float | None, float | None]:
    """(gpu_util_percent, gpu_temp_c) via ``nvidia-smi``; ``(None, None)`` off NVIDIA.

    Works on dGPU and Jetson (JetPack ships nvidia-smi). Best-effort: any
    failure just means no GPU numbers this tick.
    """
    exe = shutil.which("nvidia-smi")
    if exe is None:
        return None, None
    try:
        out = subprocess.run(  # noqa: S603
            [exe, "--query-gpu=utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return None, None
    first = out.splitlines()[0] if out else ""
    parts = [pt.strip() for pt in first.split(",")]
    if len(parts) != 2:
        return None, None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


def collect_metrics(*, hardware: Hardware | None = None) -> p.HeartbeatPayload:
    temperatures = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}
    temperature = next((item.current for group in temperatures.values() for item in group), None)

    vmem = psutil.virtual_memory()
    gpu_percent, gpu_temp = (None, None)
    if hardware is None or hardware.has_cuda:
        gpu_percent, gpu_temp = _gpu_stats()

    capabilities = None
    if hardware is not None:
        capabilities = p.DeviceCapabilities(
            arch=hardware.arch,
            is_jetson=hardware.is_jetson,
            accelerators=sorted(hardware.accelerators),
            backend=hardware.backend,
            device=hardware.device,
            encoders=sorted(hardware.encoders),
            model_formats=list(hardware.model_formats),
        )

    return p.HeartbeatPayload(
        cpu_percent=psutil.cpu_percent(interval=None),
        gpu_percent=gpu_percent,
        mem_percent=vmem.percent,
        mem_used_mb=round(vmem.used / 1024 / 1024, 1),
        mem_total_mb=round(vmem.total / 1024 / 1024, 1),
        temperature_c=temperature if temperature is not None else gpu_temp,
        capabilities=capabilities,
        recorded_at=utcnow(),
    )


__all__ = ["collect_metrics"]

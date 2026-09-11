"""Edge host metrics — **whole-machine**, not this process.

``psutil.cpu_percent`` / ``virtual_memory`` / ``disk_usage`` are already
system-wide. The one caveat is containers: psutil then sees the container's
namespaced view. Run the agent natively on the device, or mount the host's
procfs/sysfs and point psutil at them:

    docker run -v /proc:/host/proc:ro -v /sys:/host/sys:ro \
               -e HOST_PROC=/host/proc -e HOST_SYS=/host/sys ...
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess

import edge_protocol as p
import psutil
from dqh.svc_core.helpers.time import utcnow

from edge_agent.core.hardware import Hardware

logger = logging.getLogger("edge_agent.metrics")

# Point psutil at the host's procfs/sysfs when running containerised (no-op otherwise).
if _host_proc := os.getenv("HOST_PROC"):
    psutil.PROCFS_PATH = _host_proc
if _host_sys := os.getenv("HOST_SYS"):
    os.environ.setdefault("HOST_SYS", _host_sys)  # psutil reads this for sensors on Linux


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


def _cpu_temp() -> float | None:
    if not hasattr(psutil, "sensors_temperatures"):
        return None
    groups = psutil.sensors_temperatures()
    # prefer a CPU/SoC package sensor, else the first reading available
    for key in ("coretemp", "cpu_thermal", "k10temp", "soc", "thermal"):
        if key in groups and groups[key]:
            return groups[key][0].current
    return next((item.current for group in groups.values() for item in group), None)


def collect_metrics(*, hardware: Hardware | None = None) -> p.HeartbeatPayload:
    vmem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    gpu_percent, gpu_temp = (None, None)
    if hardware is None or hardware.has_cuda:
        gpu_percent, gpu_temp = _gpu_stats()
    cpu_temp = _cpu_temp()

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
        disk_percent=disk.percent,
        temperature_c=cpu_temp if cpu_temp is not None else gpu_temp,
        capabilities=capabilities,
        recorded_at=utcnow(),
    )


__all__ = ["collect_metrics"]

"""Edge host metrics helpers."""

from __future__ import annotations

import edge_protocol as p
import psutil

from dqh.svc_core.helpers.time import utcnow


def collect_metrics() -> p.HeartbeatPayload:
    temperatures = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}
    temperature = next((item.current for group in temperatures.values() for item in group), None)
    return p.HeartbeatPayload(
        cpu_percent=psutil.cpu_percent(interval=None),
        mem_percent=psutil.virtual_memory().percent,
        temperature_c=temperature,
        recorded_at=utcnow(),
    )


__all__ = ["collect_metrics"]
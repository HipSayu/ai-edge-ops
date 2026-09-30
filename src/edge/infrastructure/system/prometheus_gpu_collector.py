from hopquangdo.observability.prometheus import PrometheusScraper

from src.shared.contracts import GpuTelemetry


class PrometheusGpuCollector:
    """GpuTelemetry from dcgm-exporter. Several GPUs are folded into one node-level sample:
    mean utilisation/clock, summed memory/power, hottest temperature."""

    def __init__(self, scraper: PrometheusScraper) -> None:
        self._scraper = scraper

    async def collect(self, node_id: str) -> GpuTelemetry | None:
        s = await self._scraper.scrape()
        if s is None or not s.series("DCGM_FI_DEV_GPU_UTIL"):
            return None  # no exporter or no NVIDIA GPU on this node
        used = s.total("DCGM_FI_DEV_FB_USED")  # MiB
        free = s.total("DCGM_FI_DEV_FB_FREE")
        return GpuTelemetry(
            node_id=node_id,
            gpu_usage_pct=_round(s.mean("DCGM_FI_DEV_GPU_UTIL")),
            gpu_memory_used_mb=used,
            gpu_memory_usage_pct=round(used / (used + free) * 100, 2) if used is not None and free else None,
            gpu_frequency_mhz=_round(s.mean("DCGM_FI_DEV_SM_CLOCK")),
            gpu_power_w=_round(s.total("DCGM_FI_DEV_POWER_USAGE")),
            gpu_temperature_c=s.maximum("DCGM_FI_DEV_GPU_TEMP"),
        )


def _round(value: float | None) -> float | None:
    return round(value, 1) if value is not None else None

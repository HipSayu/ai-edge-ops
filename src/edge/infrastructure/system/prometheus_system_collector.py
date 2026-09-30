from collections.abc import Callable

from hopquangdo.observability.prometheus import Labels, MetricSnapshot, PrometheusScraper

from src.shared.contracts import NodeStatus, SystemTelemetry

_MB = 2**20
_GB = 2**30
# Virtual/loopback interfaces and partitions would double-count real traffic
_IGNORED_NICS = ("lo", "docker", "veth", "br-", "cni", "flannel", "cali", "virbr")


class PrometheusSystemCollector:
    """SystemTelemetry from node-exporter. Counters (CPU, disk, network) become rates between two scrapes,
    so the first sample after start has them unset."""

    def __init__(
        self,
        scraper: PrometheusScraper,
        mountpoint: str = "/",
        status_provider: Callable[[], NodeStatus] | None = None,
    ) -> None:
        self._scraper = scraper
        self._mountpoint = mountpoint
        self._status_provider = status_provider
        self._previous: MetricSnapshot | None = None

    async def collect(self, node_id: str) -> SystemTelemetry:
        status = self._status_provider() if self._status_provider else NodeStatus.ONLINE
        snapshot = await self._scraper.scrape()
        if snapshot is None:
            return SystemTelemetry(node_id=node_id, agent_status=status)
        previous, self._previous = self._previous, snapshot
        return SystemTelemetry(
            node_id=node_id,
            agent_status=status,
            **self._gauges(snapshot),
            **(self._rates(previous, snapshot) if previous else {}),
        )

    def _gauges(self, s: MetricSnapshot) -> dict:
        mem_total = s.first("node_memory_MemTotal_bytes")
        mem_avail = s.first("node_memory_MemAvailable_bytes")
        mem_used = mem_total - mem_avail if mem_total is not None and mem_avail is not None else None
        swap_total = s.first("node_memory_SwapTotal_bytes")
        swap_free = s.first("node_memory_SwapFree_bytes")

        on_mount = self._on_mountpoint
        fs_size = s.first("node_filesystem_size_bytes", on_mount)
        fs_avail = s.first("node_filesystem_avail_bytes", on_mount)
        inodes = s.first("node_filesystem_files", on_mount)
        inodes_free = s.first("node_filesystem_files_free", on_mount)

        now, boot = s.first("node_time_seconds"), s.first("node_boot_time_seconds")
        return {
            "cpu_load_1m": s.first("node_load1"),
            "cpu_load_5m": s.first("node_load5"),
            "memory_usage_pct": _pct(mem_used, mem_total),
            "memory_available_mb": _div(mem_avail, _MB),
            "memory_used_mb": _div(mem_used, _MB),
            "swap_usage_pct": _pct(swap_total - swap_free, swap_total) if swap_total and swap_free is not None else None,
            "disk_usage_pct": _pct(fs_size - fs_avail, fs_size) if fs_size and fs_avail is not None else None,
            "disk_free_gb": _div(fs_avail, _GB, 2),
            "inode_usage_pct": _pct(inodes - inodes_free, inodes) if inodes and inodes_free is not None else None,
            "cpu_temperature_c": s.maximum("node_hwmon_temp_celsius") or s.maximum("node_thermal_zone_temp"),
            "node_uptime_sec": round(now - boot) if now is not None and boot is not None else None,
            "process_count": _int(s.first("node_processes_pids") or s.first("node_procs_running")),
        }

    def _rates(self, prev: MetricSnapshot, cur: MetricSnapshot) -> dict:
        def delta(name: str, where=None) -> float | None:
            a, b = prev.total(name, where), cur.total(name, where)
            return b - a if a is not None and b is not None and b >= a else None  # counter reset -> skip

        # CPU shares are ratios of counter deltas, independent of wall-clock time
        cpu_all = delta("node_cpu_seconds_total")
        cpu_idle = delta("node_cpu_seconds_total", lambda l: l.get("mode") == "idle")
        cpu_iowait = delta("node_cpu_seconds_total", lambda l: l.get("mode") == "iowait")
        rates = {
            "cpu_usage_pct": _pct(cpu_all - cpu_idle, cpu_all) if cpu_all and cpu_idle is not None else None,
            "cpu_iowait_pct": _pct(cpu_iowait, cpu_all) if cpu_all and cpu_iowait is not None else None,
        }
        elapsed = cur.taken_at - prev.taken_at
        if elapsed <= 0:
            return rates
        nic = self._is_physical_nic
        return {
            **rates,
            "cpu_context_switches": _div(delta("node_context_switches_total"), elapsed),
            "disk_read_mb_s": _div(delta("node_disk_read_bytes_total"), elapsed * _MB, 3),
            "disk_write_mb_s": _div(delta("node_disk_written_bytes_total"), elapsed * _MB, 3),
            "network_rx_mb_s": _div(delta("node_network_receive_bytes_total", nic), elapsed * _MB, 3),
            "network_tx_mb_s": _div(delta("node_network_transmit_bytes_total", nic), elapsed * _MB, 3),
        }

    def _on_mountpoint(self, labels: Labels) -> bool:
        return labels.get("mountpoint") == self._mountpoint

    @staticmethod
    def _is_physical_nic(labels: Labels) -> bool:
        return not labels.get("device", "").startswith(_IGNORED_NICS)


def _pct(part: float | None, whole: float | None) -> float | None:
    return round(part / whole * 100, 2) if part is not None and whole else None


def _div(value: float | None, by: float, ndigits: int = 1) -> float | None:
    return round(value / by, ndigits) if value is not None and by else None


def _int(value: float | None) -> int | None:
    return int(value) if value is not None else None

import httpx
from hopquangdo.observability.prometheus import PrometheusScraper

from src.edge.infrastructure.system.prometheus_gpu_collector import PrometheusGpuCollector
from src.edge.infrastructure.system.prometheus_system_collector import PrometheusSystemCollector


def node_exporter_text(cpu_idle: float, cpu_user: float, rx: float) -> str:
    return f"""
# TYPE node_cpu_seconds_total counter
node_cpu_seconds_total{{cpu="0",mode="idle"}} {cpu_idle}
node_cpu_seconds_total{{cpu="0",mode="user"}} {cpu_user}
node_cpu_seconds_total{{cpu="0",mode="iowait"}} 0
# TYPE node_load1 gauge
node_load1 0.5
# TYPE node_memory_MemTotal_bytes gauge
node_memory_MemTotal_bytes 8589934592
# TYPE node_memory_MemAvailable_bytes gauge
node_memory_MemAvailable_bytes 2147483648
# TYPE node_filesystem_size_bytes gauge
node_filesystem_size_bytes{{mountpoint="/boot",fstype="vfat"}} 100
node_filesystem_size_bytes{{mountpoint="/",fstype="ext4"}} 1000
# TYPE node_filesystem_avail_bytes gauge
node_filesystem_avail_bytes{{mountpoint="/boot",fstype="vfat"}} 99
node_filesystem_avail_bytes{{mountpoint="/",fstype="ext4"}} 250
# TYPE node_network_receive_bytes_total counter
node_network_receive_bytes_total{{device="eth0"}} {rx}
node_network_receive_bytes_total{{device="lo"}} 999999999
"""


DCGM = """
# TYPE DCGM_FI_DEV_GPU_UTIL gauge
DCGM_FI_DEV_GPU_UTIL{gpu="0"} 20
DCGM_FI_DEV_GPU_UTIL{gpu="1"} 60
# TYPE DCGM_FI_DEV_FB_USED gauge
DCGM_FI_DEV_FB_USED{gpu="0"} 1000
DCGM_FI_DEV_FB_USED{gpu="1"} 3000
# TYPE DCGM_FI_DEV_FB_FREE gauge
DCGM_FI_DEV_FB_FREE{gpu="0"} 3000
DCGM_FI_DEV_FB_FREE{gpu="1"} 1000
# TYPE DCGM_FI_DEV_GPU_TEMP gauge
DCGM_FI_DEV_GPU_TEMP{gpu="0"} 55
DCGM_FI_DEV_GPU_TEMP{gpu="1"} 71
"""


def scraper_serving(*bodies: str) -> PrometheusScraper:
    responses, ticks = iter(bodies), iter(range(0, 1000, 5))  # scrapes 5 s apart
    transport = httpx.MockTransport(lambda _: httpx.Response(200, text=next(responses)))
    return PrometheusScraper(
        "http://exporter/metrics", client=httpx.AsyncClient(transport=transport), clock=lambda: float(next(ticks))
    )


async def test_system_collector_filters_labels_and_computes_rates():
    collector = PrometheusSystemCollector(
        scraper_serving(node_exporter_text(100, 100, 0), node_exporter_text(130, 170, 10 * 2**20))
    )
    first = await collector.collect("n1")
    assert first.memory_usage_pct == 75.0
    assert first.disk_usage_pct == 75.0  # "/" only, not /boot
    assert first.cpu_usage_pct is None  # counters need two scrapes

    second = await collector.collect("n1")
    assert second.cpu_usage_pct == 70.0  # 70 busy of 100 cpu-seconds
    assert second.network_rx_mb_s == 2.0  # 10 MiB over 5 s on eth0; lo ignored


async def test_gpu_collector_folds_multiple_gpus():
    gpu = await PrometheusGpuCollector(scraper_serving(DCGM)).collect("n1")
    assert gpu.gpu_usage_pct == 40.0
    assert gpu.gpu_memory_used_mb == 4000
    assert gpu.gpu_memory_usage_pct == 50.0
    assert gpu.gpu_temperature_c == 71


async def test_unreachable_exporter():
    transport = httpx.MockTransport(lambda _: httpx.Response(503))
    scraper = PrometheusScraper("http://exporter/metrics", client=httpx.AsyncClient(transport=transport))
    assert await PrometheusGpuCollector(scraper).collect("n1") is None
    system = await PrometheusSystemCollector(scraper).collect("n1")
    assert system.node_id == "n1" and system.cpu_usage_pct is None

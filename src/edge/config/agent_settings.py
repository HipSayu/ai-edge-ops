
from pydantic_settings import SettingsConfigDict

from src.shared.config import ApiKeySettings, MqttSettings, ServiceSettings


class AgentSettings(ServiceSettings, ApiKeySettings, MqttSettings):
    model_config = SettingsConfigDict(env_prefix="EDGE_", env_file=".env", extra="ignore")

    service_name: str = "edge-agent"
    cluster_id: str
    node_id: str
    agent_version: str = "0.1.0"

    api_port: int = 8081

    # Docker daemon URL; empty = DOCKER_HOST or the local socket
    docker_url: str | None = None
    # URL at which runtime containers reach this agent's local API
    agent_url_for_runtimes: str = "http://host.docker.internal:8081"

    state_dir: str = "/var/lib/edge-agent"

    # Local exporters scraped for node telemetry (host network)
    node_exporter_url: str = "http://127.0.0.1:9100/metrics"
    dcgm_exporter_url: str = "http://127.0.0.1:9400/metrics"
    scrape_timeout_sec: float = 3.0
    # Filesystem whose usage is reported, as node-exporter labels it (mountpoint, after --path.rootfs)
    disk_mountpoint: str = "/"

    state_interval_sec: float = 10.0
    telemetry_interval_sec: float = 5.0
    reconcile_interval_sec: float = 15.0
    log_interval_sec: float = 5.0

    # Node-health early warning; disabled unless a model directory (meta.json + weights.npz) is given
    health_model_dir: str | None = None
    health_db_path: str | None = None  # default: {state_dir}/health.db
    health_retention_days: float = 7.0
    health_max_rows: int = 200_000

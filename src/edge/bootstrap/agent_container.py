import os
from datetime import timedelta

from hopquangdo.containers import ContainerEngine
from hopquangdo.messaging import PubSub
from hopquangdo.observability.prometheus import PrometheusScraper

from src.edge.application.services.agent_service import AgentService
from src.edge.application.services.command_service import CommandService
from src.edge.application.services.health_service import HealthService
from src.edge.application.services.reporting import RuntimeLogService, StateReportService, TelemetryReportService
from src.edge.application.services.runtime_containers import RuntimeContainers
from src.edge.application.services.runtime_service import RuntimeService
from src.edge.config.agent_settings import AgentSettings
from src.edge.infrastructure.http.http_artifact_fetcher import HttpArtifactFetcher
from src.edge.infrastructure.messaging.mqtt_edge_publisher import MqttEdgePublisher
from src.edge.infrastructure.system.prometheus_gpu_collector import PrometheusGpuCollector
from src.edge.infrastructure.system.prometheus_system_collector import PrometheusSystemCollector
from src.edge.infrastructure.system.psutil_node_info_provider import PsutilNodeInfoProvider
from src.shared.contracts import EdgeTopics, NodeState, NodeStatus
from src.shared.infrastructure.messaging.mqtt_pubsub_factory import MqttPubSubFactory


class AgentContainer:
    """Composition root for the Edge Agent."""

    def __init__(
        self,
        settings: AgentSettings,
        pubsub: PubSub | None = None,
        engine: ContainerEngine | None = None,
        desired_state_repository=None,
    ) -> None:
        self.settings = settings
        topics = EdgeTopics(settings.cluster_id, settings.node_id)
        self.pubsub = pubsub or self._build_pubsub(settings, topics)
        self.publisher = MqttEdgePublisher(self.pubsub, topics)

        engine = engine or self._build_engine(settings)
        self.runtime_service = RuntimeService(
            engine=engine,
            containers=RuntimeContainers(settings.node_id),
            fetcher=HttpArtifactFetcher(os.path.join(settings.state_dir, "artifacts")),
            base_env={
                "AGENT_URL": settings.agent_url_for_runtimes,
                "NODE_ID": settings.node_id,
                "CLUSTER_ID": settings.cluster_id,
            },
        )
        self._scrapers = [
            PrometheusScraper(settings.node_exporter_url, settings.scrape_timeout_sec),
            PrometheusScraper(settings.dcgm_exporter_url, settings.scrape_timeout_sec),
        ]
        node_exporter, dcgm_exporter = self._scrapers
        self.state_report_service = StateReportService(
            settings.cluster_id, settings.node_id, settings.agent_version,
            self.runtime_service, PsutilNodeInfoProvider(), self.publisher,
        )
        self.command_service = CommandService(
            settings.node_id, self.runtime_service, self.publisher, self.state_report_service
        )
        self.health_service = self._build_health_service(settings)
        self.telemetry_report_service = TelemetryReportService(
            settings.node_id, self.publisher, self.runtime_service,
            PrometheusSystemCollector(node_exporter, settings.disk_mountpoint, self.state_report_service.agent_status),
            PrometheusGpuCollector(dcgm_exporter),
            observers=[self.health_service.observe] if self.health_service else [],
        )
        self.runtime_log_service = RuntimeLogService(settings.node_id, self.runtime_service, engine, self.publisher)
        self.agent_service = AgentService(
            settings.node_id, self.pubsub, self.publisher, self.runtime_service, self.command_service, self.state_report_service,
            self.telemetry_report_service, self.runtime_log_service,
            state_interval_sec=settings.state_interval_sec,
            telemetry_interval_sec=settings.telemetry_interval_sec,
            reconcile_interval_sec=settings.reconcile_interval_sec,
            log_interval_sec=settings.log_interval_sec,
            health_service=self.health_service,
        )

    def _build_health_service(self, settings: AgentSettings) -> HealthService | None:
        if not settings.health_model_dir:
            return None
        from src.edge.infrastructure.ml.numpy_health_predictor import NumpyHealthPredictor
        from src.edge.infrastructure.persistence.sqlite_health_store import SqliteHealthStore

        return HealthService(
            settings.node_id,
            NumpyHealthPredictor(settings.health_model_dir),
            SqliteHealthStore(settings.health_db_path or os.path.join(settings.state_dir, "health.db")),
            self.publisher,
            lambda: self.pubsub.is_connected,
            retention=timedelta(days=settings.health_retention_days),
            max_rows=settings.health_max_rows,
        )

    async def close(self) -> None:
        for scraper in self._scrapers:
            await scraper.close()

    @staticmethod
    def _build_pubsub(settings: AgentSettings, topics: EdgeTopics) -> PubSub:
        # Last Will: broker marks the node OFFLINE if the agent disappears without a clean shutdown.
        will = NodeState(
            cluster_id=settings.cluster_id, node_id=settings.node_id,
            agent_status=NodeStatus.OFFLINE, agent_version=settings.agent_version,
        )
        return MqttPubSubFactory.create(
            settings, f"edge-agent-{settings.node_id}", will_topic=topics.state(), will_payload=will.model_dump_json()
        )

    @staticmethod
    def _build_engine(settings: AgentSettings) -> ContainerEngine:
        from hopquangdo.containers.adapters.docker import DockerEngine
        return DockerEngine(base_url=settings.docker_url)

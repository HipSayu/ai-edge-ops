import uuid

from hopquangdo.messaging import PubSub
from redis.asyncio import Redis

from src.cloud.application.handlers.deployment_event_handler import DeploymentEventHandler
from src.cloud.application.handlers.edge_event_handler import EdgeEventHandler
from src.cloud.application.handlers.health_alarm_handler import HealthAlarmHandler
from src.cloud.application.handlers.node_state_handler import NodeStateHandler
from src.cloud.application.handlers.runtime_log_handler import RuntimeLogHandler
from src.cloud.application.handlers.telemetry_handler import TelemetryHandler
from src.cloud.application.services.auth_service import AuthService
from src.cloud.application.services.conversation_service import ConversationService
from src.cloud.application.services.deployment_service import DeploymentService
from src.cloud.application.services.entity_resolver import EntityResolver
from src.cloud.application.services.fleet_service import FleetService
from src.cloud.application.services.monitoring_service import MonitoringService
from src.cloud.application.services.node_liveness_service import NodeLivenessService
from src.cloud.application.services.user_service import UserService
from src.cloud.bootstrap.cloud_repositories import CloudRepositories
from src.cloud.config.cloud_settings import CloudSettings
from src.cloud.infrastructure.messaging.mqtt_command_publisher import MqttCommandPublisher
from src.cloud.infrastructure.persistence.postgres.postgres_chat_message_repository import PostgresChatMessageRepository
from src.cloud.infrastructure.persistence.postgres.postgres_cluster_repository import PostgresClusterRepository
from src.cloud.infrastructure.persistence.postgres.postgres_conversation_repository import (
    PostgresConversationRepository,
)
from src.cloud.infrastructure.persistence.postgres.postgres_database import PostgresDatabase
from src.cloud.infrastructure.persistence.postgres.postgres_deployment_repository import PostgresDeploymentRepository
from src.cloud.infrastructure.persistence.postgres.postgres_event_repository import PostgresEventRepository
from src.cloud.infrastructure.persistence.postgres.postgres_health_repository import PostgresHealthRepository
from src.cloud.infrastructure.persistence.postgres.postgres_node_repository import PostgresNodeRepository
from src.cloud.infrastructure.persistence.postgres.postgres_runtime_repository import PostgresRuntimeRepository
from src.cloud.infrastructure.persistence.postgres.postgres_user_repository import PostgresUserRepository
from src.cloud.infrastructure.persistence.redis.redis_refresh_token_store import RedisRefreshTokenStore
from src.cloud.infrastructure.persistence.redis.redis_runtime_log_repository import RedisRuntimeLogRepository
from src.cloud.infrastructure.persistence.redis.redis_telemetry_repository import RedisTelemetryRepository
from src.cloud.infrastructure.security.argon2_password_hasher import Argon2PasswordHasher
from src.cloud.infrastructure.security.jwt_access_token_codec import JwtAccessTokenCodec
from src.shared.contracts import EdgeTopics
from src.shared.contracts.topics import EventKind
from src.shared.infrastructure.messaging.mqtt_pubsub_factory import MqttPubSubFactory


class CloudContainer:
    """Composition root for the Cloud: wires repositories, services and MQTT consumers."""

    def __init__(
        self, settings: CloudSettings, pubsub: PubSub | None = None, repositories: CloudRepositories | None = None
    ) -> None:
        self.settings = settings
        self.pubsub = pubsub or MqttPubSubFactory.create(settings, f"{settings.service_name}-{uuid.uuid4().hex[:8]}")
        self._database: PostgresDatabase | None = None
        self._redis: Redis | None = None

        repos = repositories or self._build_repositories()
        self.clusters, self.nodes, self.runtimes = repos.clusters, repos.nodes, repos.runtimes
        self.deployments, self.telemetry_repository, self.event_repository = (
            repos.deployments, repos.telemetry, repos.events,
        )
        self.model_repository = self._build_model_repository()

        hasher = Argon2PasswordHasher()
        self.user_service = UserService(repos.users, hasher)
        self.auth_service = AuthService(
            repos.users,
            hasher,
            JwtAccessTokenCodec(settings.jwt_private_key_file.read_text(), settings.access_token_ttl_min * 60),
            repos.refresh_tokens,
            service_api_keys=settings.api_keys,
            allow_registration=settings.allow_registration,
        )

        self.conversation_service = ConversationService(repos.conversations, repos.chat_messages)
        self.fleet_service = FleetService(self.clusters, self.nodes, self.runtimes)
        # Finds entities by id, code or name for the assistant's MCP tools
        self.entity_resolver = EntityResolver(self.clusters, self.nodes, self.runtimes, self.deployments)
        self.deployment_service = DeploymentService(
            self.deployments, self.nodes, self.runtimes, MqttCommandPublisher(self.pubsub)
        )
        self.monitoring_service = MonitoringService(
            self.fleet_service, self.telemetry_repository, self.event_repository, repos.runtime_logs
        )

        self.node_state_handler = NodeStateHandler(self.nodes, self.runtimes)
        self.runtime_log_handler = RuntimeLogHandler(repos.runtime_logs)
        self.deployment_event_handler = DeploymentEventHandler(self.deployments, self.runtimes)
        self.telemetry_handler = TelemetryHandler(self.telemetry_repository, repos.health)
        self.health_alarm_handler = HealthAlarmHandler(repos.health) if repos.health is not None else None
        self.edge_event_handler = EdgeEventHandler(self.event_repository)
        self.node_liveness_service = NodeLivenessService(self.nodes, settings.node_heartbeat_timeout_sec)

    def _build_repositories(self) -> CloudRepositories:
        self._database = PostgresDatabase(self.settings.database_url)
        self._redis = Redis.from_url(self.settings.redis_url)
        return CloudRepositories(
            clusters=PostgresClusterRepository(self._database),
            nodes=PostgresNodeRepository(self._database),
            runtimes=PostgresRuntimeRepository(self._database),
            deployments=PostgresDeploymentRepository(self._database),
            telemetry=RedisTelemetryRepository(self._redis),
            events=PostgresEventRepository(self._database),
            users=PostgresUserRepository(self._database),
            refresh_tokens=RedisRefreshTokenStore(self._redis, self.settings.refresh_token_ttl_days * 86400),
            runtime_logs=RedisRuntimeLogRepository(self._redis),
            conversations=PostgresConversationRepository(self._database),
            chat_messages=PostgresChatMessageRepository(self._database),
            health=PostgresHealthRepository(self._database),
        )

    def _build_model_repository(self):
        if self.settings.model_store == "huggingface":
            from src.cloud.infrastructure.model_store.huggingface_model_repository import HuggingFaceModelRepository

            return HuggingFaceModelRepository(self.settings.hf_token, self.settings.hf_endpoint)
        return None

    async def start(self) -> None:
        if self._database is not None:
            await self._database.connect()
        await self.pubsub.connect()

    async def stop(self) -> None:
        await self.pubsub.disconnect()
        if self._redis is not None:
            await self._redis.aclose()
        if self._database is not None:
            await self._database.close()

    async def subscribe_consumers(self) -> None:
        """Worker side: consume state, deployment results, telemetry and events from all nodes."""
        await self.pubsub.subscribe(EdgeTopics.all_states(), self.node_state_handler.handle)
        await self.pubsub.subscribe(EdgeTopics.all_telemetry(), self.telemetry_handler.handle)
        await self.pubsub.subscribe(EdgeTopics.all_events(), self._on_event)
        await self.pubsub.subscribe(EdgeTopics.all_logs(), self.runtime_log_handler.handle)

    async def _on_event(self, message) -> None:
        await self.edge_event_handler.handle(message)
        kind = EdgeTopics.parse(message.topic).kind
        if kind == EventKind.DEPLOYMENT:
            await self.deployment_event_handler.handle(message)
        elif kind == EventKind.HEALTH and self.health_alarm_handler is not None:
            await self.health_alarm_handler.handle(message)

    async def check_database(self) -> bool:
        return True if self._database is None else await self._database.ping()

    async def check_redis(self) -> bool:
        return await self.telemetry_repository.ping()

    async def check_broker(self) -> bool:
        return self.pubsub.is_connected

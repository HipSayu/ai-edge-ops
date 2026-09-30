from dataclasses import dataclass

from src.cloud.application.ports.chat_message_repository import ChatMessageRepository
from src.cloud.application.ports.cluster_repository import ClusterRepository
from src.cloud.application.ports.conversation_repository import ConversationRepository
from src.cloud.application.ports.deployment_repository import DeploymentRepository
from src.cloud.application.ports.event_repository import EventRepository
from src.cloud.application.ports.health_repository import HealthRepository
from src.cloud.application.ports.node_repository import NodeRepository
from src.cloud.application.ports.refresh_token_store import RefreshTokenStore
from src.cloud.application.ports.runtime_log_repository import RuntimeLogRepository
from src.cloud.application.ports.runtime_repository import RuntimeRepository
from src.cloud.application.ports.telemetry_repository import TelemetryRepository
from src.cloud.application.ports.user_repository import UserRepository


@dataclass(frozen=True)
class CloudRepositories:
    """Every repository the Cloud needs; production builds them on Postgres + Redis, tests inject fakes."""

    clusters: ClusterRepository
    nodes: NodeRepository
    runtimes: RuntimeRepository
    deployments: DeploymentRepository
    telemetry: TelemetryRepository
    events: EventRepository
    users: UserRepository
    refresh_tokens: RefreshTokenStore
    runtime_logs: RuntimeLogRepository
    conversations: ConversationRepository
    chat_messages: ChatMessageRepository
    health: HealthRepository | None = None  # needs the V004 TimescaleDB schema

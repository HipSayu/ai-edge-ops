from src.cloud.bootstrap.cloud_repositories import CloudRepositories
from tests.fakes.cloud.fake_chat_message_repository import FakeChatMessageRepository
from tests.fakes.cloud.fake_cluster_repository import FakeClusterRepository
from tests.fakes.cloud.fake_conversation_repository import FakeConversationRepository
from tests.fakes.cloud.fake_deployment_repository import FakeDeploymentRepository
from tests.fakes.cloud.fake_event_repository import FakeEventRepository
from tests.fakes.cloud.fake_node_repository import FakeNodeRepository
from tests.fakes.cloud.fake_refresh_token_store import FakeRefreshTokenStore
from tests.fakes.cloud.fake_runtime_log_repository import FakeRuntimeLogRepository
from tests.fakes.cloud.fake_runtime_repository import FakeRuntimeRepository
from tests.fakes.cloud.fake_telemetry_repository import FakeTelemetryRepository
from tests.fakes.cloud.fake_user_repository import FakeUserRepository


class FakeCloudRepositories:
    """Dict-backed repositories so Cloud tests run without Postgres/Redis. Test-only; never used in src."""

    @staticmethod
    def create() -> CloudRepositories:
        return CloudRepositories(
            clusters=FakeClusterRepository(),
            nodes=FakeNodeRepository(),
            runtimes=FakeRuntimeRepository(),
            deployments=FakeDeploymentRepository(),
            telemetry=FakeTelemetryRepository(),
            events=FakeEventRepository(),
            users=FakeUserRepository(),
            refresh_tokens=FakeRefreshTokenStore(),
            runtime_logs=FakeRuntimeLogRepository(),
            conversations=FakeConversationRepository(),
            chat_messages=FakeChatMessageRepository(),
        )

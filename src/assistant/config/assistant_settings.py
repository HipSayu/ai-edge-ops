from pydantic_settings import SettingsConfigDict

from src.assistant.config.knowledge_settings import KnowledgeSettings
from src.assistant.config.tracing_settings import TracingSettings
from src.shared.config import ApiKeySettings, CloudApiSettings, LlmSettings, RedisSettings, ServiceSettings


class AssistantSettings(
    ServiceSettings, ApiKeySettings, LlmSettings, CloudApiSettings, RedisSettings, KnowledgeSettings, TracingSettings
):
    model_config = SettingsConfigDict(env_prefix="ASSISTANT_", env_file=(".env", ".env.local"), extra="ignore")

    service_name: str = "assistant"
    api_port: int = 8100

    # Agent: model calls per turn (the last one answers without tools), tool timeout, tool search results
    agent_max_rounds: int = 8
    tool_timeout_sec: float = 60.0

    # Chat streams and conversation memory (Redis)
    session_ttl_min: int = 7 * 24 * 60
    stream_ttl_sec: float = 600.0
    stream_idle_timeout_sec: float = 120.0

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class TracingSettings(BaseSettings):
    """Langfuse tracing of the agent (LLM calls, reasoning, tool calls, tokens and cost per chat turn).
    Off unless both keys are set; Langfuse Cloud by default, or a self-hosted Langfuse via `langfuse_host`."""

    langfuse_public_key: str | None = None
    langfuse_secret_key: SecretStr | None = None
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_environment: str = "production"

    @property
    def tracing_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)

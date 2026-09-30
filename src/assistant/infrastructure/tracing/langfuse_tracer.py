from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from src.assistant.config.tracing_settings import TracingSettings


class LangfuseTracer:
    """Sends each chat turn to Langfuse as one trace: every model call (prompt, reasoning, tokens, cost) and tool
    call of the graph, grouped by conversation (session) and user."""

    def __init__(self, settings: TracingSettings, service: str) -> None:
        self._client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key.get_secret_value() if settings.langfuse_secret_key else None,
            host=settings.langfuse_host,
            environment=settings.langfuse_environment,
        )
        self._service = service

    def callbacks(self) -> list[BaseCallbackHandler]:
        # One handler per turn: it holds that run's span tree
        return [CallbackHandler()]

    def metadata(self, session_id: str, user_id: str | None, kind: str) -> dict[str, Any]:
        """Run metadata the Langfuse handler reads to set the trace's session, user and tags."""
        metadata: dict[str, Any] = {"langfuse_session_id": session_id, "langfuse_tags": [self._service, kind]}
        if user_id:
            metadata["langfuse_user_id"] = user_id
        return metadata

    def shutdown(self) -> None:
        """Flushes buffered traces; call on application stop."""
        self._client.shutdown()

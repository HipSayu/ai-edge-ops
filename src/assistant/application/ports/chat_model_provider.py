from typing import Protocol

from langchain_core.language_models import BaseChatModel


class ChatModelProvider(Protocol):
    """Builds a chat model from a `provider:model` name (e.g. `openai:gpt-5-mini`)."""

    def create(self, name: str) -> BaseChatModel: ...

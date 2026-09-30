from __future__ import annotations

from typing import Protocol

from src.cloud.domain.entities.chat_message import ChatMessage


class ChatMessageRepository(Protocol):
    async def add(self, message: ChatMessage) -> ChatMessage: ...

    async def list_for_session(self, session_id: str) -> list[ChatMessage]:
        """Oldest first."""
        ...

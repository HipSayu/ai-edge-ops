from __future__ import annotations

from src.cloud.domain.entities.chat_message import ChatMessage
from src.shared.domain.clock import Clock


class FakeChatMessageRepository:
    def __init__(self) -> None:
        self._items: list[ChatMessage] = []

    async def add(self, message: ChatMessage) -> ChatMessage:
        message.created_at = Clock.now()
        self._items.append(message)
        return message

    async def list_for_session(self, session_id: str) -> list[ChatMessage]:
        return [m for m in self._items if m.session_id == session_id]

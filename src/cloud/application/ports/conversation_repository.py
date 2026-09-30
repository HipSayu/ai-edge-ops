from __future__ import annotations

from typing import Protocol

from src.cloud.domain.entities.conversation import Conversation


class ConversationRepository(Protocol):
    async def add(self, conversation: Conversation) -> Conversation: ...

    async def get(self, conversation_id: str) -> Conversation | None: ...

    async def list_for_user(self, user_id: str, limit: int) -> list[Conversation]:
        """Most recently active first."""
        ...

    async def save(self, conversation: Conversation) -> Conversation: ...

    async def touch(self, conversation_id: str) -> None:
        """Marks the conversation as just active (moves it to the top of the list)."""
        ...

    async def delete(self, conversation_id: str) -> None:
        """Removes the conversation and its messages (FK cascade)."""
        ...

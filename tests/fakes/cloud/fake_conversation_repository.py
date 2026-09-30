from __future__ import annotations

from datetime import timedelta

from src.cloud.domain.entities.conversation import Conversation
from src.shared.domain.clock import Clock


class FakeConversationRepository:
    def __init__(self) -> None:
        self._items: dict[str, Conversation] = {}
        self._ticks = 0

    def _now(self):
        # Strictly increasing, so "most recently active first" is deterministic within one test
        self._ticks += 1
        return Clock.now() + timedelta(microseconds=self._ticks)

    async def add(self, conversation: Conversation) -> Conversation:
        conversation.created_at = conversation.updated_at = self._now()
        self._items[conversation.id] = conversation
        return conversation

    async def get(self, conversation_id: str) -> Conversation | None:
        return self._items.get(conversation_id)

    async def list_for_user(self, user_id: str, limit: int) -> list[Conversation]:
        mine = [c for c in self._items.values() if c.user_id == user_id]
        return sorted(mine, key=lambda c: c.updated_at, reverse=True)[:limit]

    async def save(self, conversation: Conversation) -> Conversation:
        self._items[conversation.id] = conversation
        return conversation

    async def touch(self, conversation_id: str) -> None:
        if conversation_id in self._items:
            self._items[conversation_id].updated_at = self._now()

    async def delete(self, conversation_id: str) -> None:
        self._items.pop(conversation_id, None)

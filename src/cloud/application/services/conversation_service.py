from __future__ import annotations

import uuid
from typing import Any

from src.cloud.application.ports.chat_message_repository import ChatMessageRepository
from src.cloud.application.ports.conversation_repository import ConversationRepository
from src.cloud.domain.entities.chat_message import ChatMessage, ChatRole
from src.cloud.domain.entities.conversation import Conversation
from src.shared.exceptions import AppException, ErrorCode

TITLE_MAX = 80


class ConversationService:
    """A user's assistant conversations and the messages shown in them. Each user only ever sees their own:
    someone else's conversation is reported as not found. The agent's working memory is not kept here; the
    assistant holds it under the same id."""

    def __init__(self, conversations: ConversationRepository, messages: ChatMessageRepository) -> None:
        self._conversations = conversations
        self._messages = messages

    async def list(self, user_id: str, limit: int = 100) -> list[Conversation]:
        return await self._conversations.list_for_user(user_id, limit)

    async def create(self, user_id: str, title: str | None = None) -> Conversation:
        return await self._conversations.add(
            Conversation(id=str(uuid.uuid4()), user_id=user_id, title=self._title(title))
        )

    async def get(self, user_id: str, conversation_id: str) -> Conversation:
        conversation = await self._conversations.get(conversation_id) if self._is_uuid(conversation_id) else None
        if conversation is None or conversation.user_id != user_id:
            raise AppException(ErrorCode.NOT_FOUND, f"Conversation {conversation_id} not found")
        return conversation

    async def rename(self, user_id: str, conversation_id: str, title: str) -> Conversation:
        conversation = await self.get(user_id, conversation_id)
        conversation.title = self._title(title)
        return await self._conversations.save(conversation)

    async def delete(self, user_id: str, conversation_id: str) -> None:
        await self.get(user_id, conversation_id)
        await self._conversations.delete(conversation_id)

    async def messages(self, user_id: str, conversation_id: str) -> list[ChatMessage]:
        await self.get(user_id, conversation_id)
        return await self._messages.list_for_session(conversation_id)

    async def add_message(
        self, user_id: str, conversation_id: str, role: ChatRole, content: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatMessage:
        conversation = await self.get(user_id, conversation_id)
        message = await self._messages.add(
            ChatMessage(id=str(uuid.uuid4()), session_id=conversation_id, role=role, content=content,
                        metadata=metadata or {})
        )
        if conversation.title is None and role == ChatRole.USER and content:
            conversation.title = self._title(content)  # untitled: named after its first question
            await self._conversations.save(conversation)
        await self._conversations.touch(conversation_id)
        return message

    @staticmethod
    def _title(text: str | None) -> str | None:
        text = " ".join((text or "").split())
        if not text:
            return None
        return text if len(text) <= TITLE_MAX else f"{text[:TITLE_MAX - 1].rstrip()}…"

    @staticmethod
    def _is_uuid(value: str) -> bool:
        try:
            uuid.UUID(value)
        except ValueError:
            return False
        return True

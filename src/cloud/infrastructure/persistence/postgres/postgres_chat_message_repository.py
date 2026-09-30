from __future__ import annotations

from src.cloud.domain.entities.chat_message import ChatMessage, ChatRole
from src.cloud.infrastructure.persistence.postgres.postgres_repository import PostgresRepository


class PostgresChatMessageRepository(PostgresRepository[ChatMessage]):
    entity = ChatMessage

    async def add(self, message: ChatMessage) -> ChatMessage:
        added = await self._one(
            """
            INSERT INTO chat_messages (id, session_id, role, content, tool_name, tool_call_id, metadata)
            VALUES ($1::uuid, $2::uuid, $3::chat_role, $4, $5, $6, $7)
            RETURNING *
            """,
            message.id, message.session_id, message.role.value, message.content, message.tool_name,
            message.tool_call_id, message.metadata,
        )
        return self._typed(added)

    async def list_for_session(self, session_id: str) -> list[ChatMessage]:
        rows = await self._many(
            "SELECT * FROM chat_messages WHERE session_id = $1::uuid ORDER BY created_at, id", session_id
        )
        return [self._typed(m) for m in rows]

    @staticmethod
    def _typed(message: ChatMessage) -> ChatMessage:
        message.role = ChatRole(message.role)
        return message

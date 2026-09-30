from __future__ import annotations

from src.cloud.domain.entities.conversation import Conversation
from src.cloud.infrastructure.persistence.postgres.postgres_repository import PostgresRepository


class PostgresConversationRepository(PostgresRepository[Conversation]):
    entity = Conversation

    async def add(self, conversation: Conversation) -> Conversation:
        return await self._one(
            """
            INSERT INTO chat_sessions (id, user_id, title, metadata)
            VALUES ($1::uuid, $2::uuid, $3, $4)
            RETURNING *
            """,
            conversation.id, conversation.user_id, conversation.title, conversation.metadata,
        )

    async def get(self, conversation_id: str) -> Conversation | None:
        return await self._one("SELECT * FROM chat_sessions WHERE id = $1::uuid", conversation_id)

    async def list_for_user(self, user_id: str, limit: int) -> list[Conversation]:
        return await self._many(
            "SELECT * FROM chat_sessions WHERE user_id = $1::uuid ORDER BY updated_at DESC LIMIT $2", user_id, limit
        )

    async def save(self, conversation: Conversation) -> Conversation:
        return await self._one(
            "UPDATE chat_sessions SET title = $2, metadata = $3 WHERE id = $1::uuid RETURNING *",
            conversation.id, conversation.title, conversation.metadata,
        )

    async def touch(self, conversation_id: str) -> None:
        await self._execute("UPDATE chat_sessions SET updated_at = NOW() WHERE id = $1::uuid", conversation_id)

    async def delete(self, conversation_id: str) -> None:
        await self._execute("DELETE FROM chat_sessions WHERE id = $1::uuid", conversation_id)

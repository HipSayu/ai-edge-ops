"""Assistant conversation use-cases."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.assistant.models import ChatMessage
from app.modules.assistant.schemas import ChatMessageCreate


class AssistantService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_messages(self) -> list[ChatMessage]:
        return list((await self.session.scalars(select(ChatMessage).order_by(ChatMessage.id))).all())

    async def send_message(self, data: ChatMessageCreate) -> ChatMessage:
        message = ChatMessage(
            role="user",
            text=data.text,
            created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

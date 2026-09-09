"""Assistant conversation use-cases: store messages, run slash commands / the agent."""

from __future__ import annotations

import datetime as dt

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.assistant.commands import parse
from app.modules.assistant.models import ChatMessage
from app.modules.assistant.operator_agent import OperatorAssistant
from app.modules.assistant.schemas import ChatMessageCreate

_HISTORY_TURNS = 12


class AssistantService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_messages(self) -> list[ChatMessage]:
        return list(
            (await self.session.scalars(select(ChatMessage).order_by(ChatMessage.id))).all()
        )

    async def send_message(self, data: ChatMessageCreate) -> ChatMessage:
        """Persist the user turn, produce an assistant reply, persist + return it."""
        await self._add("user", data.text)

        cmd, arg = parse(data.text)
        if cmd is not None and cmd.kind == "control" and cmd.name == "clear":
            await self.session.execute(select(ChatMessage))  # no-op to keep a txn
            for row in await self.list_messages():
                await self.session.delete(row)
            await self.session.commit()
            return await self._add("assistant", "Conversation cleared.")

        if cmd is not None and cmd.kind == "direct":
            reply = await cmd.handler(arg)  # type: ignore[misc]
        else:
            query = cmd.prompt if (cmd and cmd.kind == "prompt") else data.text
            if cmd and arg:
                query = f"{query}\n\n(user note: {arg})"
            reply = await OperatorAssistant().answer(query, history=await self._history())

        return await self._add("assistant", reply)

    async def _history(self) -> list[BaseMessage]:
        rows = await self.list_messages()
        turns = rows[-(_HISTORY_TURNS + 1) : -1]  # exclude the just-added user turn
        out: list[BaseMessage] = []
        for r in turns:
            out.append(HumanMessage(r.text) if r.role == "user" else AIMessage(r.text))
        return out

    async def _add(self, role: str, text: str) -> ChatMessage:
        message = ChatMessage(
            role=role, text=text, created_at=dt.datetime.now(dt.timezone.utc).isoformat()
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message


__all__ = ["AssistantService"]

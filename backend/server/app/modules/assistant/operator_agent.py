"""The operator assistant — a ReAct agent over the domain tools."""

from __future__ import annotations

from functools import lru_cache

from dqh.ai_core import Agent
from langchain_core.messages import AIMessage, BaseMessage

from app.modules.assistant.toolset import langchain_tools

SYSTEM_PROMPT = (
    "You are the AI Edge Ops operator assistant. Answer questions about the edge "
    "fleet, model deployments, PPE violations, alerts and analytics using the "
    "tools. Be concise and specific — cite device ids, counts and timestamps. "
    "If a question is ambiguous, make a reasonable assumption and say so. Never "
    "invent data that a tool did not return."
)


@lru_cache(maxsize=1)
def _agent() -> Agent:
    return Agent.create(langchain_tools(), model=None, system=SYSTEM_PROMPT)


class OperatorAssistant:
    async def answer(self, query: str, history: list[BaseMessage] | None = None) -> str:
        messages = await _agent().run(query, history=history)
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and isinstance(msg.content, str) and msg.content.strip():
                return msg.content
        return "(no answer)"


__all__ = ["OperatorAssistant", "SYSTEM_PROMPT"]

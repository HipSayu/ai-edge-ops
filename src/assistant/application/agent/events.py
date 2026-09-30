import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig


class StreamEventName(StrEnum):
    """Internal custom events dispatched by graph nodes; AgentOrchestrator turns them into public events."""

    DELTA = "agent.delta"
    REASONING = "agent.reasoning"
    TOOLS_START = "tools.start"


@dataclass(frozen=True)
class StreamEvent:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_sse(self) -> str:
        return f"event: {self.name}\ndata: {json.dumps(self.payload, ensure_ascii=False, default=str)}\n\n"


class EventEmitter:
    """Dispatches a node's progress as LangGraph custom events (surfaced by `astream_events`)."""

    @staticmethod
    async def delta(content: str, config: RunnableConfig) -> None:
        await adispatch_custom_event(StreamEventName.DELTA, {"content": content}, config=config)

    @staticmethod
    async def reasoning(content: str, config: RunnableConfig) -> None:
        await adispatch_custom_event(StreamEventName.REASONING, {"content": content}, config=config)

    @staticmethod
    async def tools_start(calls: list[dict], config: RunnableConfig) -> None:
        tools = [{"id": call["id"], "name": call["name"], "args": call["args"]} for call in calls]
        await adispatch_custom_event(StreamEventName.TOOLS_START, {"tools": tools}, config=config)

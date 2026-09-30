import logging
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from src.assistant.application.agent.events import StreamEvent, StreamEventName
from src.assistant.application.agent.tools_node import Decision
from src.assistant.application.helpers.text import to_text, truncate
from src.assistant.application.ports.tracer import Tracer

logger = logging.getLogger(__name__)

ERROR_TEXT = "Đã có lỗi xảy ra, vui lòng thử lại."
EMPTY_REPLY_TEXT = "Xin lỗi, tôi chưa có câu trả lời."
TRACE_OUTPUT_CHARS = 2000


class AgentOrchestrator:
    """Runs or resumes one chat turn and translates graph events into public stream events.

    Public events: reasoning* / status* / tool_end* / token*, then either `done` (the turn finished) or `approval_required`
    (the turn is paused on write tool calls; answer with `resume`), or a single `error`.
    Tokens of a round that ends up calling tools are superseded: `done.reply` is the answer.
    Conversation history and paused turns live in the checkpointer under thread_id=session_id.
    With a tracer, each turn is also traced (Langfuse) under the session and the user who asked.
    """

    def __init__(
        self, graph: CompiledStateGraph, recursion_limit: int = 50, tracer: Tracer | None = None
    ) -> None:
        self._graph = graph
        self._recursion_limit = recursion_limit
        self._tracer = tracer

    def _config(self, session_id: str) -> dict:
        return {"configurable": {"thread_id": session_id}, "recursion_limit": self._recursion_limit}

    def _turn_config(self, session_id: str, user_id: str | None, kind: str) -> dict:
        config = {**self._config(session_id), "run_name": f"chat.{kind}"}
        if self._tracer is not None:
            config["callbacks"] = self._tracer.callbacks()
            config["metadata"] = self._tracer.metadata(session_id, user_id, kind)
        return config

    async def pending_approval(self, session_id: str) -> dict | None:
        snapshot = await self._graph.aget_state(self._config(session_id))
        return snapshot.interrupts[0].value if snapshot.interrupts else None

    async def run(self, session_id: str, message: str, user_id: str | None = None) -> AsyncIterator[StreamEvent]:
        """A new user message. If the session is paused on approvals, the message answers them as "other"."""
        pending = await self.pending_approval(session_id)
        if pending:
            decisions = {r["tool_call_id"]: {"decision": "other", "message": message} for r in pending["requests"]}
            graph_input: Any = Command(resume=decisions, update={"rounds": 0})
        else:
            graph_input = {"messages": [HumanMessage(content=message)], "rounds": 0}
        async for event in self._stream(session_id, graph_input, self._turn_config(session_id, user_id, "turn")):
            yield event

    async def resume(
        self, session_id: str, decisions: dict[str, Decision], user_id: str | None = None
    ) -> AsyncIterator[StreamEvent]:
        """The user's decisions on the paused write tool calls, keyed by tool_call_id."""
        if not await self.pending_approval(session_id):
            yield StreamEvent("error", {"message": "Không có thao tác nào đang chờ duyệt."})
            return
        config = self._turn_config(session_id, user_id, "approval")
        async for event in self._stream(session_id, Command(resume=decisions), config):
            yield event

    async def _stream(self, session_id: str, graph_input: Any, config: dict) -> AsyncIterator[StreamEvent]:
        try:
            async for event in self._graph.astream_events(graph_input, config=config, version="v2"):
                kind, data = event["event"], event.get("data") or {}
                if kind == "on_custom_event":
                    payload = data if isinstance(data, dict) else {}
                    if event["name"] == StreamEventName.DELTA:
                        yield StreamEvent("token", {"content": payload.get("content", "")})
                    elif event["name"] == StreamEventName.REASONING:
                        yield StreamEvent("reasoning", {"content": payload.get("content", "")})
                    elif event["name"] == StreamEventName.TOOLS_START:
                        yield StreamEvent("status", {"type": "TOOLS", "tools": payload.get("tools", [])})
                elif kind == "on_tool_end":
                    yield StreamEvent("tool_end", self._tool_end(event.get("name"), data.get("output")))
            snapshot = await self._graph.aget_state(config)
        except Exception:
            logger.exception("agent graph failed session_id=%s", session_id)
            yield StreamEvent("error", {"message": ERROR_TEXT})
            return

        if snapshot.interrupts:
            yield StreamEvent("approval_required", {"session_id": session_id, **snapshot.interrupts[0].value})
            return
        messages = snapshot.values.get("messages", [])
        last = messages[-1] if messages else None
        reply = last.text.strip() if isinstance(last, AIMessage) else ""
        yield StreamEvent("done", {"reply": reply or EMPTY_REPLY_TEXT, "session_id": session_id})

    @staticmethod
    def _tool_end(name: str | None, output: Any) -> dict:
        """The tool's result for the trace shown to the user, cut to TRACE_OUTPUT_CHARS."""
        content = getattr(output, "content", output)
        text = truncate(to_text(content), TRACE_OUTPUT_CHARS)
        return {
            "id": getattr(output, "tool_call_id", None), "tool": name,
            "status": getattr(output, "status", "success"), "output": text,
        }

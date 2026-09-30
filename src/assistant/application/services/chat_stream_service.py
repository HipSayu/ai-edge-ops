"""One chat turn: POST creates a stream and runs the agent in the background; GET consumes it as SSE.

User message / approval -> ChatStreamService -> AgentOrchestrator/LangGraph -> StreamQueue (Redis) -> SSE
"""

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any

from src.assistant.application.agent.events import StreamEvent
from src.assistant.application.agent.orchestrator import AgentOrchestrator
from src.assistant.application.agent.tools_node import Decision
from src.assistant.application.ports.stream_queue import StreamQueue

logger = logging.getLogger(__name__)


class ChatStreamService:
    def __init__(self, orchestrator: AgentOrchestrator, queue: StreamQueue) -> None:
        self._orchestrator = orchestrator
        self._queue = queue
        self._tasks: set[asyncio.Task] = set()

    async def create_stream(self, session_id: str, message: str, user_id: str | None = None) -> str:
        return await self._start(session_id, self._orchestrator.run(session_id, message, user_id))

    async def create_approval_stream(
        self, session_id: str, decisions: dict[str, Decision], user_id: str | None = None
    ) -> str:
        """Resumes a turn paused on write tool calls with the user's decision for each."""
        return await self._start(session_id, self._orchestrator.resume(session_id, decisions, user_id))

    async def subscribe(self, stream_id: str) -> AsyncIterator[str] | None:
        return await self._queue.subscribe(stream_id)

    async def ask(self, session_id: str, message: str, user_id: str | None = None) -> dict[str, Any]:
        """Non-streaming turn: same pipeline, collected into one reply (or the pending approval)."""
        result: dict[str, Any] = {"session_id": session_id, "answer": "", "approval": None}
        async for event in self._orchestrator.run(session_id, message, user_id):
            match event.name:
                case "error":
                    raise RuntimeError(event.payload.get("message"))
                case "done":
                    result["answer"] = event.payload.get("reply", "")
                case "approval_required":
                    result["approval"] = event.payload
        return result

    async def stop(self) -> None:
        for task in list(self._tasks):
            task.cancel()

    async def _start(self, session_id: str, events: AsyncIterator[StreamEvent]) -> str:
        stream_id = str(uuid.uuid4())
        await self._queue.open(stream_id)
        task = asyncio.create_task(self._produce(stream_id, events), name=f"chat-stream-{stream_id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        logger.info("chat stream created stream_id=%s session_id=%s", stream_id, session_id)
        return stream_id

    async def _produce(self, stream_id: str, events: AsyncIterator[StreamEvent]) -> None:
        try:
            async for event in events:
                await self._queue.put(stream_id, event.to_sse())
        except Exception:
            logger.exception("chat stream failed stream_id=%s", stream_id)
            await self._queue.put(stream_id, StreamEvent("error", {"message": "Đã có lỗi xảy ra."}).to_sse())
        finally:
            await self._queue.close(stream_id)

import asyncio
import logging
from collections.abc import Iterable, Sequence
from typing import Any

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool

from src.assistant.application.helpers.text import to_text
from src.assistant.application.helpers.tool_calls import call_signature

logger = logging.getLogger(__name__)


class ToolRunner:
    """Runs an AIMessage's tool_calls in parallel -> ToolMessages in the same order.

    Unknown tool / exception / timeout become a ToolMessage with status="error" for the model;
    nothing is raised, so one bad tool never breaks the chat turn.
    Duplicate calls (same name + args) in one batch run once.
    """

    def __init__(self, tools: Iterable[BaseTool], timeout: float = 60.0, max_concurrency: int = 8) -> None:
        self._tools = {tool.name: tool for tool in tools}
        self._timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def run(self, calls: Sequence[dict], config: Any = None) -> list[ToolMessage]:
        unique: dict[str, dict] = {}
        for call in calls:
            unique.setdefault(call_signature(call), call)
        outputs = await asyncio.gather(*(self._execute(call, config) for call in unique.values()))
        by_signature = dict(zip(unique, outputs))
        messages = []
        for call in calls:
            content, status = by_signature[call_signature(call)]
            messages.append(ToolMessage(content=content, tool_call_id=call["id"], name=call["name"], status=status))
        return messages

    async def _execute(self, call: dict, config: Any) -> tuple[str, str]:
        name, args = call["name"], call["args"]
        tool = self._tools.get(name)
        if tool is None:
            return f"Tool error: unknown tool '{name}'. Valid tools: {', '.join(self._tools)}", "error"
        try:
            async with self._semaphore:
                result = await asyncio.wait_for(tool.ainvoke(args, config=config), timeout=self._timeout)
        except asyncio.TimeoutError:
            logger.warning("tool timeout name=%s timeout=%ss", name, self._timeout)
            return f"Tool error: '{name}' timed out after {self._timeout}s", "error"
        except Exception as exc:  # noqa: BLE001 - reported back to the model
            logger.exception("tool failed name=%s args=%s", name, args)
            return f"Tool error: {exc}", "error"
        return to_text(result), "success"

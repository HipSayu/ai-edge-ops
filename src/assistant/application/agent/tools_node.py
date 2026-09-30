import json
import logging
from typing import Literal, TypedDict

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from src.assistant.application.agent.events import EventEmitter
from src.assistant.application.prompts.prompt_loader import PromptLoader
from src.assistant.application.tools.registry import ToolRegistry
from src.assistant.application.tools.tool_runner import ToolRunner
from src.assistant.application.tools.tool_search import ACTIVATED_KEY

logger = logging.getLogger(__name__)

META_TOOLS = ("search_tools", "search_knowledge")


class Decision(TypedDict, total=False):
    """The user's answer for one write tool call: run it, refuse it, or refuse it with instructions."""

    decision: Literal["approve", "reject", "other"]
    message: str


class ToolsNode:
    """Runs the agent's tool calls. Write calls pause the graph (`interrupt`) until the user decides on each.

    Nothing runs before the interrupt, and a resumed node starts over, so read calls run exactly once:
    together with the approved write calls, after the decision.
    """

    name = "tools"

    def __init__(self, registry: ToolRegistry, runner: ToolRunner) -> None:
        self._registry = registry
        self._runner = runner

    async def __call__(self, state: dict, config: RunnableConfig) -> dict:
        calls = state["messages"][-1].tool_calls
        writes = [call for call in calls if self._registry.is_write(call["name"])]
        decisions: dict[str, Decision] = interrupt(self.approval_request(writes)) if writes else {}

        refused = {
            call["id"]: self._refusal(decisions.get(call["id"], {"decision": "reject"}))
            for call in writes if decisions.get(call["id"], {}).get("decision") != "approve"
        }
        runnable = [call for call in calls if call["id"] not in refused]
        if runnable:
            await EventEmitter.tools_start(runnable, config)
        ran = {m.tool_call_id: m for m in await self._runner.run(runnable, config)}
        messages = [
            ran[call["id"]] if call["id"] in ran
            else ToolMessage(content=refused[call["id"]], tool_call_id=call["id"], name=call["name"], status="error")
            for call in calls
        ]
        return {"messages": messages, "active_tools": self._activated(messages)}

    @staticmethod
    def approval_request(writes: list[dict]) -> dict:
        return {
            "type": "tool_approval",
            "requests": [{"tool_call_id": c["id"], "name": c["name"], "args": c["args"]} for c in writes],
        }

    @staticmethod
    def _refusal(decision: Decision) -> str:
        instructions = (decision.get("message") or "").strip()
        if decision.get("decision") == "other" and instructions:
            return PromptLoader.render("approval_other", instructions=instructions)
        return PromptLoader.load("approval_rejected")

    def _activated(self, messages: list[ToolMessage]) -> list[str]:
        names: list[str] = []
        for message in messages:
            if message.name not in META_TOOLS or message.status == "error":
                continue
            try:
                names += json.loads(message.content).get(ACTIVATED_KEY, [])
            except (ValueError, AttributeError):
                logger.warning("unreadable %s result, no tools activated", message.name)
        return self._registry.known(names)

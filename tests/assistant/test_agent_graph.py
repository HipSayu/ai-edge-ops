"""The single-agent graph: tool activation through search_tools, and human-in-the-loop approval of write tools."""

from typing import Any

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import InMemorySaver

from src.assistant.application.agent.agent_node import AgentNode
from src.assistant.application.agent.graph import ChatGraph
from src.assistant.application.agent.orchestrator import AgentOrchestrator
from src.assistant.application.agent.tools_node import ToolsNode
from src.assistant.application.tools.registry import ToolRegistry
from src.assistant.application.tools.tool_runner import ToolRunner


class ScriptedModel(BaseChatModel):
    """Replies with the scripted messages in order; records which tools each call had bound."""

    script: list[AIMessage]
    bound: list[list[str]] = []
    pending_tools: list[str] = []

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):
        clone = self.model_copy()
        clone.pending_tools = [t.name for t in tools]
        return clone

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        self.bound.append(self.pending_tools)
        return ChatResult(generations=[ChatGeneration(message=self.script.pop(0))])


def call(name: str, call_id: str, **args: Any) -> dict:
    return {"name": name, "args": args, "id": call_id, "type": "tool_call"}


@pytest.fixture
def fleet():
    calls: list[tuple[str, dict]] = []

    def tool(name: str, description: str) -> StructuredTool:
        async def run(node_id: str = "", runtime_id: str = "", action: str = "") -> dict:
            args = {k: v for k, v in {"node_id": node_id, "runtime_id": runtime_id, "action": action}.items() if v}
            calls.append((name, args))
            return {"ok": name}

        return StructuredTool.from_function(coroutine=run, name=name, description=description)

    tools = [tool("get_node", "Get one edge node"), tool("control_runtime", "Start/stop/restart a runtime")]
    search_tools = StructuredTool.from_function(
        coroutine=lambda query: _async({"tools": [], "activated_tools": ["get_node", "control_runtime", "nope"]}),
        name="search_tools", description="Find tools",
    )
    return calls, ToolRegistry([search_tools], tools)


async def _async(value):
    return value


def orchestrator(model: ScriptedModel, registry: ToolRegistry) -> AgentOrchestrator:
    graph = ChatGraph(AgentNode(model, registry), ToolsNode(registry, ToolRunner(registry.all())))
    return AgentOrchestrator(graph.build(InMemorySaver()))


async def events(stream) -> list:
    return [e async for e in stream]


async def test_search_tools_activates_tools_for_the_next_round(fleet):
    calls, registry = fleet
    model = ScriptedModel(script=[
        AIMessage(content="", tool_calls=[call("search_tools", "t1", query="node info")]),
        AIMessage(content="", tool_calls=[call("get_node", "t2", node_id="n1")]),
        AIMessage(content="Node **n1** đang ONLINE."),
    ])
    out = await events(orchestrator(model, registry).run("s1", "node n1 thế nào?"))

    assert model.bound[0] == ["search_tools"]  # starts with the meta tool only
    assert model.bound[1] == ["search_tools", "get_node", "control_runtime"]  # unknown "nope" dropped
    assert calls == [("get_node", {"node_id": "n1"})]
    assert out[-1].name == "done" and out[-1].payload["reply"] == "Node **n1** đang ONLINE."


async def test_write_tool_waits_for_approval_and_reads_run_once(fleet):
    calls, registry = fleet
    model = ScriptedModel(script=[
        AIMessage(content="", tool_calls=[call("search_tools", "t1", query="restart")]),
        AIMessage(content="", tool_calls=[
            call("get_node", "t2", node_id="n1"), call("control_runtime", "t3", runtime_id="r1", action="restart"),
        ]),
        AIMessage(content="Đã restart runtime r1."),
    ])
    agent = orchestrator(model, registry)

    paused = await events(agent.run("s1", "restart runtime r1"))
    assert paused[-1].name == "approval_required"
    assert paused[-1].payload["requests"] == [
        {"tool_call_id": "t3", "name": "control_runtime", "args": {"runtime_id": "r1", "action": "restart"}}
    ]
    assert calls == []  # nothing in the paused round ran, reads included

    done = await events(agent.resume("s1", {"t3": {"decision": "approve"}}))
    assert done[-1].name == "done" and done[-1].payload["reply"] == "Đã restart runtime r1."
    assert calls == [("get_node", {"node_id": "n1"}), ("control_runtime", {"runtime_id": "r1", "action": "restart"})]


@pytest.mark.parametrize(
    ("decision", "expected"),
    [({"decision": "reject"}, "TỪ CHỐI"), ({"decision": "other", "message": "chỉ stop thôi"}, "chỉ stop thôi")],
)
async def test_refused_write_is_reported_to_the_agent(fleet, decision, expected):
    calls, registry = fleet
    model = ScriptedModel(script=[
        AIMessage(content="", tool_calls=[call("search_tools", "t1", query="restart")]),
        AIMessage(content="", tool_calls=[call("control_runtime", "t3", runtime_id="r1", action="restart")]),
        AIMessage(content="Đã hủy."),
    ])
    agent = orchestrator(model, registry)
    await events(agent.run("s1", "restart r1"))
    await events(agent.resume("s1", {"t3": decision}))

    assert calls == []
    snapshot = await agent._graph.aget_state(agent._config("s1"))
    refusal = [m for m in snapshot.values["messages"] if isinstance(m, ToolMessage) and m.tool_call_id == "t3"][0]
    assert expected in refusal.content and refusal.status == "error"


async def test_new_message_while_paused_answers_as_other(fleet):
    calls, registry = fleet
    model = ScriptedModel(script=[
        AIMessage(content="", tool_calls=[call("search_tools", "t1", query="restart")]),
        AIMessage(content="", tool_calls=[call("control_runtime", "t3", runtime_id="r1", action="restart")]),
        AIMessage(content="Ok, chỉ dừng runtime."),
    ])
    agent = orchestrator(model, registry)
    await events(agent.run("s1", "restart r1"))
    out = await events(agent.run("s1", "thôi, chỉ stop thôi"))

    assert out[-1].name == "done" and calls == []
    assert await agent.pending_approval("s1") is None


async def test_resume_without_pending_approval_is_an_error(fleet):
    _, registry = fleet
    out = await events(orchestrator(ScriptedModel(script=[]), registry).resume("s1", {"x": {"decision": "approve"}}))
    assert [e.name for e in out] == ["error"]

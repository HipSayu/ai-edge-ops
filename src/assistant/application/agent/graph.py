from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.assistant.application.agent.agent_node import AgentNode
from src.assistant.application.agent.state import GraphState
from src.assistant.application.agent.tools_node import ToolsNode
from src.assistant.application.helpers.tool_calls import has_tool_calls


class ChatGraph:
    """START -> agent <-> tools -> END. One agent (LLM); `tools` only executes, pausing for approval of writes."""

    def __init__(self, agent: AgentNode, tools: ToolsNode) -> None:
        self.agent = agent
        self.tools = tools

    def build(self, checkpointer: BaseCheckpointSaver | None = None) -> CompiledStateGraph:
        builder = StateGraph(GraphState)
        builder.add_node(self.agent.name, self.agent)
        builder.add_node(self.tools.name, self.tools)
        builder.add_edge(START, self.agent.name)
        builder.add_conditional_edges(
            self.agent.name, lambda s: self.tools.name if has_tool_calls(s) else END,
            {self.tools.name: self.tools.name, END: END},
        )
        builder.add_edge(self.tools.name, self.agent.name)
        # The interrupt needs a checkpointer to hold the paused turn
        return builder.compile(checkpointer=checkpointer)

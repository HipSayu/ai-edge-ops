import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, SystemMessage
from langchain_core.messages.utils import message_chunk_to_message
from langchain_core.runnables import RunnableConfig

from src.assistant.application.agent.events import EventEmitter
from src.assistant.application.prompts.prompt_loader import PromptLoader
from src.assistant.application.helpers.tool_calls import drop_empty_args
from src.assistant.application.tools.registry import ToolRegistry
from src.shared.domain.clock import Clock

logger = logging.getLogger(__name__)


class AgentNode:
    """The single agent: one model call per round, with core + activated tools bound.

    A reply without tool calls is the answer; its tokens are streamed as they arrive, and so is the model's
    reasoning (summary) when the model has it enabled. Text written in a round
    that ends with tool calls is streamed too, and superseded: `done.reply` carries the final answer.
    """

    name = "agent"

    def __init__(self, model: BaseChatModel, registry: ToolRegistry, max_rounds: int = 8) -> None:
        self._model = model
        self._registry = registry
        self._max_rounds = max_rounds

    async def __call__(self, state: dict, config: RunnableConfig) -> dict:
        rounds = state.get("rounds", 0) + 1
        system = PromptLoader.render("agent", now=Clock.now().strftime("%Y-%m-%d %H:%M UTC"))
        if rounds >= self._max_rounds:
            model = self._model
            system = f"{system}\n\n{PromptLoader.load('last_round')}"
        else:
            model = self._model.bind_tools(self._registry.bound(state.get("active_tools", [])))

        full: AIMessageChunk | None = None
        async for chunk in model.astream([SystemMessage(content=system), *state["messages"]], config=config):
            full = chunk if full is None else full + chunk
            for block in chunk.content_blocks:
                if block["type"] == "reasoning" and block.get("reasoning"):
                    await EventEmitter.reasoning(block["reasoning"], config)
            if chunk.text:
                await EventEmitter.delta(chunk.text, config)
        message: AIMessage = message_chunk_to_message(full) if full is not None else AIMessage(content="")
        if message.tool_calls:
            message.tool_calls = drop_empty_args(message.tool_calls)
        logger.info("agent round=%d tool_calls=%s", rounds, [c["name"] for c in message.tool_calls])
        return {"messages": [message], "rounds": rounds}

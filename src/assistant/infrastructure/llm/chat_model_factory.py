from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from src.shared.config import LlmSettings

# Anthropic extended thinking: token budget per fixed effort (max_tokens must exceed it)
THINKING_BUDGET = {"low": 2048, "medium": 4096, "high": 8192}
# OpenAI has no "auto" effort and omitting it means "none" (never reasons). The effort is a ceiling the model
# reasons up to only as needed (measured: 0 reasoning tokens for a greeting, ~1k for a root-cause question).
OPENAI_AUTO_EFFORT = "medium"


class ChatModelFactory:
    """The one place that knows how to build chat models; swap providers here."""

    def __init__(self, settings: LlmSettings) -> None:
        self._settings = settings

    def create(self, name: str) -> BaseChatModel:
        kwargs: dict[str, Any] = {"api_key": self._settings.llm_api_key} if self._settings.llm_api_key else {}
        effort = self._settings.llm_reasoning_effort
        if effort == "off":
            kwargs["temperature"] = self._settings.llm_temperature
        elif name.startswith("openai:"):
            # Responses API: reasoning summaries stream as `reasoning` content blocks
            openai_effort = OPENAI_AUTO_EFFORT if effort == "auto" else effort
            kwargs.update(use_responses_api=True, reasoning={"effort": openai_effort, "summary": "auto"})
        elif name.startswith("anthropic:") and effort == "auto":
            # Adaptive thinking: Claude decides per request whether and how much to think
            kwargs.update(thinking={"type": "adaptive"}, max_tokens=16384)
        elif name.startswith("anthropic:"):
            budget = THINKING_BUDGET[effort]
            kwargs.update(thinking={"type": "enabled", "budget_tokens": budget}, max_tokens=budget + 8192)
        return init_chat_model(name, **kwargs)

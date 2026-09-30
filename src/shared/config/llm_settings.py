from typing import Literal

from pydantic_settings import BaseSettings


class LlmSettings(BaseSettings):
    """Models as "<provider>:<model>" for langchain's init_chat_model."""

    llm_model: str = "anthropic:claude-sonnet-5"
    llm_api_key: str | None = None  # None falls back to the provider's own env var (e.g. ANTHROPIC_API_KEY)
    llm_temperature: float = 0.0
    # Reasoning / extended thinking for models that support it. "auto" lets the model decide per
    # request whether and how much to think (a greeting: not at all; a root-cause analysis: a lot). When on, the
    # model's reasoning (summary) is streamed to the user and temperature is left to the provider.
    llm_reasoning_effort: Literal["auto", "low", "medium", "high", "off"] = "auto"

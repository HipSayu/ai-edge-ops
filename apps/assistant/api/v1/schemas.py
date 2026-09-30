from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, max_length=128, description="Omit to start a new conversation.")
    message: str = Field(
        min_length=1, max_length=8000,
        description="While write actions await approval, a message answers all of them as 'other'.",
    )


class ChatReply(BaseModel):
    session_id: str
    answer: str
    approval: dict[str, Any] | None = Field(default=None, description="Set when the turn waits for approval.")


class ChatStreamCreated(BaseModel):
    stream_id: str
    session_id: str


class ToolDecision(BaseModel):
    tool_call_id: str
    decision: Literal["approve", "reject", "other"]
    message: str | None = Field(default=None, max_length=4000, description="Instructions instead, for 'other'.")


class ApprovalRequest(BaseModel):
    decisions: list[ToolDecision] = Field(min_length=1, description="One per pending write tool call.")

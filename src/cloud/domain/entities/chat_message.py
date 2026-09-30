from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class ChatRole(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"
    TOOL = "TOOL"


@dataclass(slots=True)
class ChatMessage:
    """One message of a conversation as shown to the user (table chat_messages). An assistant reply keeps its
    reasoning trace (reasoning, tool calls and results) in `metadata`."""

    id: str
    session_id: str
    role: ChatRole
    content: str | None = None
    tool_name: str | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Conversation:
    """One assistant chat thread of a user (table chat_sessions). Its id is also the assistant's session id,
    under which the agent keeps its own working memory."""

    id: str
    user_id: str
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

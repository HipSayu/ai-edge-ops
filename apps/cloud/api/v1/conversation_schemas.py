"""Conversation request/response models. camelCase on the wire, like the auth models the dashboard reads."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class ConversationCreate(_Camel):
    title: str | None = Field(default=None, max_length=255, description="Omit to name it after the first question.")


class ConversationUpdate(_Camel):
    title: str = Field(min_length=1, max_length=255)


class ConversationOut(_Camel):
    id: str = Field(description="Also the assistant session_id to chat in this conversation.")
    title: str | None
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(_Camel):
    role: Literal["USER", "ASSISTANT"]
    content: str = Field(max_length=100_000)
    metadata: dict[str, Any] = Field(default_factory=dict, description="e.g. the reply's reasoning trace.")


class ChatMessageOut(_Camel):
    id: str
    role: str
    content: str | None
    metadata: dict[str, Any]
    created_at: datetime

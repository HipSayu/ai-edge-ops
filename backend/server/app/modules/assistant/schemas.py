"""Assistant API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    text: str
    created_at: str


class ChatMessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


class SlashCommandOut(BaseModel):
    cmd: str
    desc: str
    kind: str

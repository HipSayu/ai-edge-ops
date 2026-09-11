"""Operator assistant HTTP adapter."""

from __future__ import annotations

from dqh.svc_core.transports.http import ApiResponse, ok
from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.modules.assistant.commands import COMMANDS
from app.modules.assistant.schemas import ChatMessageCreate, ChatMessageOut, SlashCommandOut
from app.modules.assistant.service import AssistantService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/messages", response_model=ApiResponse[list[ChatMessageOut]])
async def list_messages(db: DbSession) -> ApiResponse[list[ChatMessageOut]]:
    rows = await AssistantService(db).list_messages()
    return ok([ChatMessageOut.model_validate(row) for row in rows])


@router.post(
    "/messages",
    response_model=ApiResponse[ChatMessageOut],
    status_code=status.HTTP_201_CREATED,
)
async def send_message(data: ChatMessageCreate, db: DbSession) -> ApiResponse[ChatMessageOut]:
    reply = await AssistantService(db).send_message(data)
    return ok(ChatMessageOut.model_validate(reply))


@router.get("/commands", response_model=ApiResponse[list[SlashCommandOut]])
async def list_commands() -> ApiResponse[list[SlashCommandOut]]:
    return ok(
        [SlashCommandOut(cmd=f"/{c.name}", desc=c.desc, kind=c.kind) for c in COMMANDS.values()]
    )


__all__ = ["router"]

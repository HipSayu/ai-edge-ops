"""Operator assistant HTTP adapter."""

from __future__ import annotations

from dqh.svc_core.transports.http import ApiResponse, ok
from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.modules.assistant.schemas import ChatMessageCreate, ChatMessageOut
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
    message = await AssistantService(db).send_message(data)
    return ok(ChatMessageOut.model_validate(message))

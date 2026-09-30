import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from apps.assistant.api.v1.schemas import ApprovalRequest, ChatReply, ChatRequest, ChatStreamCreated
from apps.assistant.dependencies import get_chat_stream_service
from src.assistant.application.services.chat_stream_service import ChatStreamService

router = APIRouter(prefix="/chat", tags=["chat"])


def user_id(x_auth_subject: str | None = Header(default=None, include_in_schema=False)) -> str | None:
    """The signed-in user, as verified by the API gateway (None for service API keys)."""
    return x_auth_subject


@router.post("", response_model=ChatReply)
async def chat(
    body: ChatRequest,
    user: str | None = Depends(user_id),
    service: ChatStreamService = Depends(get_chat_stream_service),
):
    return await service.ask(body.session_id or str(uuid.uuid4()), body.message, user)


@router.post("/stream", response_model=ChatStreamCreated)
async def create_chat_stream(
    body: ChatRequest,
    user: str | None = Depends(user_id),
    service: ChatStreamService = Depends(get_chat_stream_service),
):
    """Starts the turn in the background; open GET /chat/stream/{stream_id} to receive it."""
    session_id = body.session_id or str(uuid.uuid4())
    return ChatStreamCreated(stream_id=await service.create_stream(session_id, body.message, user), session_id=session_id)


@router.post("/{session_id}/approval", response_model=ChatStreamCreated)
async def approve(
    session_id: str,
    body: ApprovalRequest,
    user: str | None = Depends(user_id),
    service: ChatStreamService = Depends(get_chat_stream_service),
):
    """Answers an `approval_required` event (approve / reject / other + instructions, per tool call) and resumes
    the turn; open GET /chat/stream/{stream_id} to receive the rest of it."""
    decisions = {d.tool_call_id: d.model_dump(exclude={"tool_call_id"}, exclude_none=True) for d in body.decisions}
    stream_id = await service.create_approval_stream(session_id, decisions, user)
    return ChatStreamCreated(stream_id=stream_id, session_id=session_id)


@router.get("/stream/{stream_id}")
async def get_chat_stream(stream_id: str, service: ChatStreamService = Depends(get_chat_stream_service)):
    """SSE events: status, tool_end, token, then done | approval_required | error.
    `done.reply` is the answer (tokens of rounds that went on to call tools are superseded)."""
    frames = await service.subscribe(stream_id)
    if frames is None:
        raise HTTPException(status_code=404, detail="Stream not found or already consumed.")
    return StreamingResponse(
        frames, media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

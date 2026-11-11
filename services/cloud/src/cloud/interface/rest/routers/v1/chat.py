"""The chat with the assistant: the web app's own endpoints, answered by an agent that lives in Dunly.

A chat is two calls: POST /chat starts the turn and answers with the id of its stream, GET /chat/stream/{id} carries
the events as the agent writes them. The user's token goes on to the agent with every turn."""

import json

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import Response, StreamingResponse

from cloud.interface.rest.deps import current_user, get_container
from cloud.interface.rest.schemas.chat import ApprovalIn, ChatIn, ChatStartedOut, ImageOut, ModelsOut
from cloud.bootstrap.container import Container
from shared.http import bearer_token
from shared.viewer import Viewer

router = APIRouter(prefix="/chat", tags=["chat"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("", response_model=ChatStartedOut)
def start(
    body: ChatIn, request: Request, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)
):
    """Starts a chat turn. A missing assistant or a bad request fails here, as a plain error."""
    started = container.chat.start(viewer, bearer_token(request), body.message, body.session_id, body.image_ids)
    return ChatStartedOut(stream_id=started.stream_id, session_id=started.session_id)


@router.get("/stream/{stream_id}")
def stream(stream_id: str, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    """The events of a started turn as server-sent events, as the agent writes them. Readable once."""
    events = container.chat.events(viewer, stream_id)
    return StreamingResponse(
        (_sse(name, data) for name, data in events), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/models", response_model=ModelsOut)
def models(viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    default, choices = container.chat.models()
    return ModelsOut(default=default, models=choices)


@router.post("/images", response_model=ImageOut)
async def upload_image(
    file: UploadFile, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container),
):
    """Attaches a picture (JPEG, PNG or WebP, up to 8 MB) to send with the next message."""
    return ImageOut(image_id=container.chat_images.attach(viewer, await file.read()))


@router.get("/images/{image_id}")
def image(image_id: str, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    """A picture of this viewer's chat: one they attached, or one the detector marked."""
    content, media_type = container.chat_images.read(viewer, image_id)
    return Response(content, media_type=media_type, headers={"Cache-Control": "private, max-age=3600"})


@router.post("/approvals/{proposal_id}")
def decide(
    proposal_id: str, body: ApprovalIn, request: Request,
    viewer: Viewer = Depends(current_user), container: Container = Depends(get_container),
):
    """The user approves or rejects a change the assistant proposed. The agent applies it with the user's token."""
    return {"message": container.chat.decide(viewer, bearer_token(request), proposal_id, body.approve)}

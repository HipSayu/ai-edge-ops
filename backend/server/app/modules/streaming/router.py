"""Streaming HTTP adapter: token issuance + the MediaMTX auth webhook.

No media traffic touches this process — video goes straight edge <-> MediaMTX
<-> frontend over WHIP/WHEP. This router only decides *who* is allowed to
publish/read *which* camera path.
"""

from __future__ import annotations

from dqh.svc_core.transports.http import ApiResponse, ok
from fastapi import APIRouter, Depends, Response, status

from app.core.auth import require_permission
from app.modules.streaming.schemas import StreamAuthCheck, StreamTokenOut
from app.modules.streaming.service import StreamingService

router = APIRouter(prefix="/streaming", tags=["streaming"])


@router.get("/cameras/{camera_id}/view-token", response_model=ApiResponse[StreamTokenOut])
async def get_view_token(
    camera_id: int, _: object = Depends(require_permission("cameras.stream.view"))
) -> ApiResponse[StreamTokenOut]:
    return ok(StreamingService().issue_view_token(camera_id))


@router.get("/cameras/{camera_id}/publish-token", response_model=ApiResponse[StreamTokenOut])
async def get_publish_token(
    camera_id: int, _: object = Depends(require_permission("cameras.stream.publish"))
) -> ApiResponse[StreamTokenOut]:
    # For an operator manually (re)starting a stream from the dashboard. The
    # edge agent itself never calls this over HTTP — it asks for its token
    # over the existing MQTT link instead (see AgentGateway._on_stream_token_request
    # / EdgeLink.request_stream_token), since it has no HTTP credential.
    return ok(StreamingService().issue_publish_token(camera_id))


@router.post("/auth", status_code=status.HTTP_204_NO_CONTENT)
async def mediamtx_auth_webhook(check: StreamAuthCheck, response: Response) -> None:
    """Called by MediaMTX (``authMethod: http``) before every publish/read.

    Only ``publish`` and ``read`` are ours to gate; anything else (the
    MediaMTX API/metrics probes) we don't issue tokens for, so deny by
    default.
    """
    token = check.token or check.password
    if check.action in ("publish", "read") and StreamingService().verify(
        token, path=check.path, action=check.action
    ):
        return
    response.status_code = status.HTTP_401_UNAUTHORIZED


__all__ = ["router"]

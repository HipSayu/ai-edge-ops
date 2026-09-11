"""Streaming HTTP adapter: token issuance + the MediaMTX auth webhook.

No media traffic touches this process — video goes straight edge <-> MediaMTX
<-> frontend over WHIP/WHEP. This router only decides *who* is allowed to
publish/read *which* camera path.
"""

from __future__ import annotations

import logging
from urllib.parse import parse_qs

from dqh.svc_core.transports.http import ApiResponse, ok
from fastapi import APIRouter, Depends, Response, status

from app.modules.iam.bearer_auth import require_permission
from app.modules.streaming.schemas import StreamAuthCheck, StreamTokenOut
from app.modules.streaming.service import StreamingService

logger = logging.getLogger("app.streaming")

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


def _token_from(check: StreamAuthCheck) -> str:
    """The bearer token, wherever MediaMTX put it.

    ``authMethod: http`` forwards HTTP Basic creds as ``user``/``password`` and a
    JWT (from ``Authorization: Bearer`` or ``?jwt=``) as ``token`` — but ffmpeg's
    WHIP muxer sends neither an auth header nor Basic creds, so the edge publisher
    passes the token in the URL query. Check every spot.
    """
    if check.token:
        return check.token
    if check.password:
        return check.password
    qs = parse_qs(check.query or "")
    for key in ("jwt", "token", "pass", "password", "access_token"):
        if qs.get(key):
            return qs[key][0]
    return ""


@router.post("/auth", status_code=status.HTTP_204_NO_CONTENT)
async def mediamtx_auth_webhook(check: StreamAuthCheck, response: Response) -> None:
    """Called by MediaMTX (``authMethod: http``) before every publish/read.

    Only ``publish`` and ``read`` are ours to gate; anything else (the
    MediaMTX API/metrics probes) we don't issue tokens for, so deny by
    default.
    """
    token = _token_from(check)
    allowed = check.action in ("publish", "read") and StreamingService().verify(
        token, path=check.path, action=check.action
    )
    if not allowed:
        logger.info(
            "mediamtx auth DENY: action=%s path=%s proto=%s token_len=%d query=%r",
            check.action, check.path, check.protocol, len(token), check.query,
        )
        response.status_code = status.HTTP_401_UNAUTHORIZED


__all__ = ["router"]

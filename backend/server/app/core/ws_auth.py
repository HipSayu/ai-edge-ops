"""Authenticate a browser WebSocket before it joins the hub.

FastAPI dependencies don't run for ``@router.websocket`` routes, so the WS
endpoints pass this as ``serve_ws(..., authenticate=...)``. It runs *before*
``websocket.accept()``; raising rejects the socket with close code 1008.

Token source, in order: ``?token=`` query param (browsers can't set headers on
``new WebSocket``), then an ``Authorization: Bearer`` header. In
``ENVIRONMENT=local`` an anonymous socket is allowed, matching
:func:`app.core.bearer_auth.require_permission`.
"""

from __future__ import annotations

from fastapi import WebSocket, status
from fastapi.exceptions import WebSocketException

from app.core.config import settings
from app.core.database import session_scope
from app.core.token_codec import decode_token
from app.modules.user.models import User


def _extract_token(websocket: WebSocket) -> str | None:
    token = websocket.query_params.get("token")
    if token:
        return token
    header = websocket.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:]
    return None


async def authenticate_ws(websocket: WebSocket) -> User | None:
    token = _extract_token(websocket)
    if token is None:
        if settings.environment == "local":
            return None
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="authentication required")

    try:
        user_id = decode_token(token, "access")
    except Exception as exc:  # decode_token raises HTTPException; normalise for WS
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="invalid token"
        ) from exc

    async with session_scope() as session:
        user = await session.get(User, user_id)
    if user is None or not user.active:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="user is inactive or missing"
        )
    websocket.state.user = user
    return user


__all__ = ["authenticate_ws"]

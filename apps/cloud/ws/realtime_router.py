"""WebSocket /ws — live edge state, telemetry and events.

Connect:  ws://host/api/v1/ws?topics=edge/+/+/state,edge/<cluster>/<node>/telemetry/+&token=<access token | API key>
Client → server (optional, to change filters at runtime):
    {"action": "subscribe", "topics": ["edge/+/+/event/+"]}
    {"action": "unsubscribe", "topics": ["edge/+/+/state"]}
Server → client:
    {"topic": "...", "payload": {...}, "timestamp": "..."}
    {"action": "ack", "topics": [...]}   after each subscribe/unsubscribe
"""

import asyncio
import contextlib
from urllib.parse import unquote

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from apps.cloud.dependencies import get_auth_service, get_realtime_service
from src.cloud.application.services.realtime_service import RealtimeSubscription
from src.shared.exceptions import AppException

router = APIRouter(tags=["realtime"])

DEFAULT_TOPICS = "edge/#"


@router.websocket("/ws")
async def realtime(
    websocket: WebSocket,
    topics: str = Query(DEFAULT_TOPICS),
    token: str | None = Query(None, description="User access token or service API key"),
    api_key: str | None = Query(None, description="Deprecated alias of `token`"),
):
    # Browsers cannot set headers on a WebSocket, so the credential comes in the query string
    try:
        await get_auth_service().authenticate(token or api_key or websocket.headers.get("x-api-key"))
    except AppException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    realtime_service = get_realtime_service()
    await websocket.accept()
    sub = realtime_service.subscribe(_parse(_raw_query_param(websocket, "topics") or topics))
    sender = asyncio.create_task(_send_loop(websocket, sub))
    try:
        while True:
            _apply_control(sub, await websocket.receive_json())
            # ack goes through the same queue so it is ordered with streamed messages
            sub.offer({"action": "ack", "topics": sorted(sub.filters)})
    except (WebSocketDisconnect, ValueError):
        pass
    finally:
        realtime_service.unsubscribe(sub)
        sender.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sender


async def _send_loop(websocket: WebSocket, sub: RealtimeSubscription) -> None:
    while True:
        await websocket.send_json(await sub.queue.get())


def _apply_control(sub: RealtimeSubscription, message: dict) -> None:
    requested = {t for t in message.get("topics", []) if isinstance(t, str) and t.startswith("edge/")}
    if message.get("action") == "subscribe":
        sub.filters |= requested
    elif message.get("action") == "unsubscribe":
        sub.filters -= requested


def _raw_query_param(websocket: WebSocket, name: str) -> str | None:
    """Query value decoded with `unquote` (not `unquote_plus`) so MQTT `+` wildcards survive unencoded."""
    for pair in websocket.scope.get("query_string", b"").decode("latin-1").split("&"):
        key, _, value = pair.partition("=")
        if key == name:
            return unquote(value)
    return None


def _parse(topics: str) -> set[str]:
    return {t.strip() for t in topics.split(",") if t.strip().startswith("edge/")} or {DEFAULT_TOPICS}

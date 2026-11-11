"""ASGI middleware: gives each request an id and logs its result once, when the response has been sent.

Pure ASGI (not BaseHTTPMiddleware) so streamed responses (SSE, MJPEG) flow through untouched and the line is written
when the stream ends, with the real duration. Only the path is logged, never the query string: media links carry the
access token there."""

import logging
import time
from collections.abc import Awaitable, Callable, Iterable, MutableMapping
from typing import Any

from trace_id.context import REQUEST_ID_HEADER, _request_id, accept

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]

_HEADER = REQUEST_ID_HEADER.lower().encode("latin-1")
log = logging.getLogger("trace_id")


class RequestLogMiddleware:
    def __init__(
        self,
        app: Callable[[Scope, Receive, Send], Awaitable[None]],
        service: str = "app",
        quiet_paths: Iterable[str] = ("/health", "/api/health"),
    ) -> None:
        self.app = app
        self.service = service
        self.quiet_paths = frozenset(quiet_paths)  # health probes would drown everything else

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # lifespan, websocket
            await self.app(scope, receive, send)
            return

        incoming = next((v.decode("latin-1") for k, v in scope["headers"] if k == _HEADER), None)
        rid = accept(incoming)
        scope.setdefault("state", {})["request_id"] = rid
        token = _request_id.set(rid)
        status, error = 500, None  # 500 until a response starts: a crash before that is what the client sees
        started = time.perf_counter()

        async def send_with_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != _HEADER]
                headers.append((_HEADER, rid.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except BaseException as exc:
            error = exc
            raise
        finally:
            try:
                self._report(scope, status, started, error)
            finally:
                _request_id.reset(token)

    def _report(self, scope: Scope, status: int, started: float, error: BaseException | None) -> None:
        if error is None and scope["path"] in self.quiet_paths and status < 500:
            return
        extra = {
            "http_method": scope["method"], "http_path": scope["path"], "http_status": status,
            "duration_ms": round((time.perf_counter() - started) * 1000, 1),
        }
        line = f"{scope['method']} {scope['path']} -> {status} in {extra['duration_ms']}ms"
        if isinstance(error, Exception):
            log.error(f"{line} (unhandled {type(error).__name__})", exc_info=error, extra=extra)
        elif error is not None:  # cancelled: the client went away before the response was finished
            log.info(f"{line} (client disconnected)", extra=extra)
        else:
            level = logging.ERROR if status >= 500 else logging.WARNING if status >= 400 else logging.INFO
            log.log(level, line, extra=extra)

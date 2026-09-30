from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from src.cloud.application.services.auth_service import AuthService
from src.shared.exceptions import AppException


class McpAuthGuard:
    """ASGI wrapper for the mounted MCP app (mounts skip FastAPI dependencies).

    Same credentials as REST: `Authorization: Bearer <access token | API key>` or `X-API-Key`.
    """

    def __init__(self, app: ASGIApp, auth: AuthService) -> None:
        self._app = app
        self._auth = auth

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            authorization = headers.get(b"authorization", b"").decode()
            credential = authorization[7:].strip() if authorization.lower().startswith("bearer ") else None
            try:
                await self._auth.authenticate(credential or headers.get(b"x-api-key", b"").decode() or None)
            except AppException as exc:
                await JSONResponse({"detail": exc.message}, status_code=401)(scope, receive, send)
                return
        await self._app(scope, receive, send)

"""API gateway: the single entry point for users and services. Run: python -m apps.gateway.main

    dashboard nginx (:80) -> gateway (:8200) -> /api/v1/chat*   -> assistant (:8100)
                                             -> everything else -> cloud     (:8000)

Access tokens are verified here with the Cloud's public key (the Cloud keeps the private key and is the only
one issuing tokens); upstreams receive the verified identity as X-Auth-Subject / X-Auth-Role.
"""

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
from hopquangdo.http import ServiceRunner
from hopquangdo.observability import LoggingSetup

from src.gateway.auth.jwt_verifier import JwtVerifier
from src.gateway.auth.request_authenticator import RequestAuthenticator, Unauthorized
from src.gateway.config.gateway_settings import GatewaySettings
from src.gateway.proxy.http_proxy import HttpProxy
from src.gateway.proxy.websocket_proxy import WebSocketProxy
from src.gateway.routing.route_table import RouteTable

METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]


def create_app(settings: GatewaySettings) -> FastAPI:
    authenticator = RequestAuthenticator(JwtVerifier(settings.jwt_public_key_file.read_text(), settings.jwt_issuer))
    routes = RouteTable({"/api/v1/chat": settings.assistant_url}, default=settings.cloud_url)
    http = HttpProxy(settings.connect_timeout_sec)
    ws = WebSocketProxy()
    app = FastAPI(title="Edge Ops API Gateway", docs_url=None, redoc_url=None, openapi_url=None)
    app.router.add_event_handler("shutdown", http.close)

    @app.get("/gateway/health", include_in_schema=False)
    async def health():
        return {"status": "ok"}

    @app.websocket("/{path:path}")
    async def websocket_route(websocket: WebSocket, path: str):
        try:
            identity = authenticator.identity(websocket.url.path, websocket.headers, websocket.query_params)
        except Unauthorized:
            await websocket.close(code=4401)
            return
        await ws.bridge(websocket, routes.upstream(websocket.url.path), identity)

    @app.api_route("/{path:path}", methods=METHODS, include_in_schema=False)
    async def http_route(request: Request, path: str):
        try:
            identity = authenticator.identity(request.url.path, request.headers, request.query_params)
        except Unauthorized as exc:
            return JSONResponse({"error": {"code": "unauthorized", "message": str(exc), "details": {}}}, 401)
        return await http.forward(request, routes.upstream(request.url.path), identity)

    return app


if __name__ == "__main__":
    settings = GatewaySettings()
    LoggingSetup.configure(settings.service_name, settings.log_level, settings.log_json)
    ServiceRunner.run(create_app(settings), settings.api_host, settings.api_port)

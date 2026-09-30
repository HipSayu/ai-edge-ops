import httpx
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import StreamingResponse

from src.gateway.auth.request_authenticator import IDENTITY_HEADERS

# Hop-by-hop headers (RFC 9110 §7.6.1) are per connection and never forwarded; nor are client-sent identities
DROPPED_REQUEST_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer",
    "transfer-encoding", "upgrade", "host", "content-length", *IDENTITY_HEADERS,
}
DROPPED_RESPONSE_HEADERS = {"connection", "keep-alive", "transfer-encoding", "content-length"}


class HttpProxy:
    """Forwards one HTTP request upstream and streams the response back (SSE included, no buffering)."""

    def __init__(self, connect_timeout: float) -> None:
        # No read timeout: chat streams stay open while the agent works
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(None, connect=connect_timeout), follow_redirects=False)

    async def forward(self, request: Request, upstream: str, identity: dict[str, str]) -> StreamingResponse:
        headers = [(k, v) for k, v in request.headers.items() if k.lower() not in DROPPED_REQUEST_HEADERS]
        client_ip = request.client.host if request.client else ""
        headers += [("x-forwarded-for", request.headers.get("x-forwarded-for", client_ip)), *identity.items()]
        body = await request.body()
        outgoing = self._client.build_request(
            request.method, f"{upstream}{request.url.path}", params=request.query_params,
            headers=headers, content=body,
        )
        response = await self._client.send(outgoing, stream=True)
        return StreamingResponse(
            response.aiter_raw(), status_code=response.status_code,
            headers={k: v for k, v in response.headers.items() if k.lower() not in DROPPED_RESPONSE_HEADERS},
            background=BackgroundTask(response.aclose),
        )

    async def close(self) -> None:
        await self._client.aclose()

import asyncio
import contextlib

import websockets
from starlette.websockets import WebSocket, WebSocketDisconnect


class WebSocketProxy:
    """Bridges a client WebSocket to the same path upstream, relaying frames both ways until either side closes."""

    async def bridge(self, client: WebSocket, upstream: str, identity: dict[str, str]) -> None:
        url = f"{upstream.replace('http', 'ws', 1)}{client.url.path}"
        if client.url.query:
            url = f"{url}?{client.url.query}"
        try:
            upstream_ws = await websockets.connect(url, additional_headers=identity, open_timeout=10)
        except (OSError, websockets.InvalidHandshake):
            await client.close(code=1011)
            return
        await client.accept()
        async with upstream_ws:
            tasks = [
                asyncio.create_task(self._to_upstream(client, upstream_ws)),
                asyncio.create_task(self._to_client(upstream_ws, client)),
            ]
            _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
        with contextlib.suppress(RuntimeError):
            await client.close()

    @staticmethod
    async def _to_upstream(client: WebSocket, upstream_ws) -> None:
        with contextlib.suppress(WebSocketDisconnect, websockets.ConnectionClosed):
            while True:
                message = await client.receive()
                if message["type"] == "websocket.disconnect":
                    return
                await upstream_ws.send(message["text"] if message.get("text") is not None else message["bytes"])

    @staticmethod
    async def _to_client(upstream_ws, client: WebSocket) -> None:
        with contextlib.suppress(websockets.ConnectionClosed, RuntimeError):
            async for frame in upstream_ws:
                if isinstance(frame, str):
                    await client.send_text(frame)
                else:
                    await client.send_bytes(frame)

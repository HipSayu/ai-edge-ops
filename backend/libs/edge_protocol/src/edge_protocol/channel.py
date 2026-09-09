"""Newline-framed ``Envelope`` transport for the agent <-> vision-runtime link.

`MessageChannel` is the seam. `UnixSocketChannel` is the real transport (the two
containers share a socket file over a volume); `channel_pair()` gives two wired
in-memory channels for tests.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Protocol

from dqh.svc_core.contracts.messaging import Envelope


class MessageChannel(Protocol):
    async def send(self, envelope: Envelope) -> None: ...
    def messages(self) -> AsyncIterator[Envelope]: ...
    async def aclose(self) -> None: ...


def _encode(envelope: Envelope) -> bytes:
    return (json.dumps(envelope.model_dump(mode="json"), separators=(",", ":")) + "\n").encode()


def _decode(line: bytes) -> Envelope:
    return Envelope.model_validate(json.loads(line))


class StreamChannel:
    """A `MessageChannel` over an asyncio reader/writer pair."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self._reader = reader
        self._writer = writer

    async def send(self, envelope: Envelope) -> None:
        self._writer.write(_encode(envelope))
        await self._writer.drain()

    async def messages(self) -> AsyncIterator[Envelope]:
        while True:
            line = await self._reader.readline()
            if not line:
                break
            yield _decode(line)

    async def aclose(self) -> None:
        self._writer.close()
        try:
            await self._writer.wait_closed()
        except Exception:  # noqa: BLE001 - close is best-effort
            ...


class UnixSocketChannel:
    """Connect (client) or accept one connection (server) on a unix socket path."""

    @staticmethod
    async def connect(path: str) -> StreamChannel:
        reader, writer = await asyncio.open_unix_connection(path)
        return StreamChannel(reader, writer)

    @staticmethod
    async def serve_one(path: str) -> StreamChannel:
        got: asyncio.Future[StreamChannel] = asyncio.get_event_loop().create_future()

        async def _on_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            if not got.done():
                got.set_result(StreamChannel(reader, writer))

        server = await asyncio.start_unix_server(_on_client, path=path)
        channel = await got
        server.close()
        return channel


class MemoryChannel:
    def __init__(self, inbox: asyncio.Queue, outbox: asyncio.Queue) -> None:
        self._in = inbox
        self._out = outbox

    async def send(self, envelope: Envelope) -> None:
        await self._out.put(envelope)

    async def messages(self) -> AsyncIterator[Envelope]:
        while True:
            env = await self._in.get()
            if env is None:
                break
            yield env

    async def aclose(self) -> None:
        await self._out.put(None)


def channel_pair() -> tuple[MemoryChannel, MemoryChannel]:
    """Two channels where a.send() is readable on b.messages(), and vice versa."""
    a_to_b: asyncio.Queue = asyncio.Queue()
    b_to_a: asyncio.Queue = asyncio.Queue()
    return MemoryChannel(b_to_a, a_to_b), MemoryChannel(a_to_b, b_to_a)


__all__ = [
    "MemoryChannel",
    "MessageChannel",
    "StreamChannel",
    "UnixSocketChannel",
    "channel_pair",
]

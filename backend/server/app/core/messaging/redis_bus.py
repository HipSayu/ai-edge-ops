"""Redis pub/sub :class:`MessageBus` — cross-replica fan-out for the WS hub.

The in-process :class:`~dqh.svc_core.transports.websocket.hub.WebSocketMessageBus`
only reaches sockets attached to *this* process. Behind a load balancer a
browser may land on replica A while the edge sample arrives at replica B, so
live pushes need a shared bus.

Only the WS fan-out path uses this (telemetry / logs / alerts) — best-effort,
latest-wins data where a dropped frame is corrected by the next one. Anything
needing delivery guarantees (commands, violations) stays on MQTT.

Wildcards: callers use MQTT syntax (``+`` one level, ``#`` the rest); we
``PSUBSCRIBE`` a widened Redis glob and re-filter every delivery through
:func:`~dqh.svc_core.messaging.topics.topic_matches`, so semantics match the
in-process bus exactly.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import redis.asyncio as redis
from dqh.svc_core.contracts.messaging import (
    Codec,
    Envelope,
    MessageBus,
    MessageHandler,
    Subscription,
)
from dqh.svc_core.helpers.messaging import JsonCodec, decode_envelope, encode_envelope
from dqh.svc_core.messaging.errors import NotConnectedError
from dqh.svc_core.messaging.topics import topic_matches

logger = logging.getLogger("app.core.messaging.redis")


def _to_redis_pattern(topic: str) -> str:
    """MQTT topic/filter -> Redis glob. ``a/+/c`` -> ``a/*/c``; ``a/#`` -> ``a/*``."""
    out: list[str] = []
    for segment in topic.split("/"):
        if segment == "#":
            out.append("*")
            break
        out.append("*" if segment == "+" else segment)
    return "/".join(out)


class _Subscription(Subscription):
    def __init__(self, bus: RedisPubSubMessageBus, topic: str, handler: MessageHandler) -> None:
        self.topic = topic
        self.handler = handler
        self._bus = bus

    async def unsubscribe(self) -> None:
        await self._bus._remove(self)


class RedisPubSubMessageBus(MessageBus):
    def __init__(
        self,
        url: str,
        *,
        codec: Codec | None = None,
        max_connections: int = 20,
    ) -> None:
        self._url = url
        self._codec = codec or JsonCodec()
        self._max_connections = max_connections
        self._redis: redis.Redis | None = None
        self._pubsub: redis.client.PubSub | None = None
        self._reader: asyncio.Task[None] | None = None
        self._subs: list[_Subscription] = []
        self._patterns: dict[str, int] = {}  # redis glob -> refcount
        self._lock = asyncio.Lock()

    # --- lifecycle ----------------------------------------------------------
    @property
    def connected(self) -> bool:
        return self._redis is not None

    async def connect(self) -> None:
        if self._redis is not None:
            return
        self._redis = redis.from_url(
            self._url, max_connections=self._max_connections, decode_responses=False
        )
        self._pubsub = self._redis.pubsub(ignore_subscribe_messages=True)
        # the reader starts on the first psubscribe — redis-py's PubSub raises if
        # polled with no channels/patterns registered
        logger.info("redis realtime bus connected (%s)", self._url)

    async def aclose(self) -> None:
        if self._reader is not None:
            self._reader.cancel()
            self._reader = None
        if self._pubsub is not None:
            await self._pubsub.aclose()
            self._pubsub = None
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
        self._subs.clear()
        self._patterns.clear()

    # --- pub/sub ----------------------------------------------------------
    async def publish(self, topic: str, envelope: Envelope[Any]) -> None:
        if self._redis is None:
            raise NotConnectedError("redis realtime bus is not connected")
        await self._redis.publish(topic, encode_envelope(envelope, self._codec))

    async def subscribe(self, topic: str, handler: MessageHandler) -> Subscription:
        if self._pubsub is None:
            raise NotConnectedError("redis realtime bus is not connected")
        sub = _Subscription(self, topic, handler)
        pattern = _to_redis_pattern(topic)
        async with self._lock:
            self._subs.append(sub)
            if self._patterns.get(pattern, 0) == 0:
                await self._pubsub.psubscribe(pattern)
            self._patterns[pattern] = self._patterns.get(pattern, 0) + 1
            if self._reader is None:
                self._reader = asyncio.create_task(self._read_loop(), name="redis-ws-reader")
        return sub

    async def _remove(self, sub: _Subscription) -> None:
        pattern = _to_redis_pattern(sub.topic)
        async with self._lock:
            try:
                self._subs.remove(sub)
            except ValueError:
                return
            self._patterns[pattern] -= 1
            if self._patterns[pattern] <= 0:
                self._patterns.pop(pattern, None)
                if self._pubsub is not None:
                    await self._pubsub.punsubscribe(pattern)

    # --- reader ---------------------------------------------------------
    async def _read_loop(self) -> None:
        assert self._pubsub is not None
        while True:
            if not self._patterns:
                await asyncio.sleep(0.1)
                continue
            try:
                message = await self._pubsub.get_message(timeout=1.0)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 - keep the loop alive across redis blips
                logger.warning("redis realtime reader hiccup", exc_info=True)
                await asyncio.sleep(0.5)
                continue
            if message is None or message.get("type") != "pmessage":
                continue
            await self._dispatch(
                message["channel"].decode(), message["data"]
            )

    async def _dispatch(self, topic: str, data: bytes) -> None:
        targets = [s for s in list(self._subs) if topic_matches(s.topic, topic)]
        if not targets:
            return
        envelope = decode_envelope(data, self._codec)
        for sub in targets:
            try:
                await sub.handler(envelope.model_copy(deep=True))
            except Exception:  # noqa: BLE001 - one bad socket must not stall the rest
                logger.warning("realtime subscriber failed (topic=%s)", sub.topic, exc_info=True)


__all__ = ["RedisPubSubMessageBus"]

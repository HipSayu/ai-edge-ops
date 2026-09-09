"""Realtime fan-out bus for the browser WebSocket hub.

``memory`` (default) keeps everything in-process — fine for a single replica,
tests, and local dev. ``redis`` fans pushes out across replicas via Redis
pub/sub. Publish call sites never change; only :func:`build_realtime_bus` does.
"""

from __future__ import annotations

import logging

from dqh.svc_core.contracts.messaging import MessageBus
from dqh.svc_core.transports.websocket.hub import WebSocketMessageBus

from app.core.config import Settings
from app.core.config import settings as default_settings

logger = logging.getLogger("app.core.messaging")


def build_realtime_bus(settings: Settings = default_settings) -> MessageBus:
    if settings.realtime_transport == "redis":
        from app.core.messaging.redis_bus import RedisPubSubMessageBus

        logger.info("realtime transport: redis")
        return RedisPubSubMessageBus(
            settings.redis.url, max_connections=settings.redis.max_connections
        )
    return WebSocketMessageBus()


__all__ = ["build_realtime_bus"]

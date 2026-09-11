"""Builds the realtime fan-out bus for the browser WebSocket hub.

``memory`` (default) keeps everything in-process — fine for a single replica,
tests, and local dev. ``redis`` fans pushes out across replicas via Redis
pub/sub (``dqh.svc_core.transports.event_driven.redis``). Publish call sites
never change; only this factory does.
"""

from __future__ import annotations

import logging

from dqh.svc_core.contracts.messaging import MessageBus
from dqh.svc_core.transports.websocket.hub import WebSocketMessageBus

from app.core.config import Settings
from app.core.config import settings as default_settings

logger = logging.getLogger("app.core.messaging")


class RealtimeBusFactory:
    def __init__(self, settings: Settings = default_settings) -> None:
        self._settings = settings

    def build(self) -> MessageBus:
        if self._settings.realtime_transport == "redis":
            from dqh.svc_core.transports.event_driven.redis import RedisPubSubMessageBus

            logger.info("realtime transport: redis")
            return RedisPubSubMessageBus(
                self._settings.redis.url,
                max_connections=self._settings.redis.max_connections,
            )
        return WebSocketMessageBus()


__all__ = ["RealtimeBusFactory"]

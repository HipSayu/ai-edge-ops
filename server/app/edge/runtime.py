"""Build the edge MessageBus + FleetGateway for the app lifespan."""

from __future__ import annotations

import logging

from dqh.svc_core.messaging import InMemoryMessageBus, MessageBus

from app.core.config import settings
from app.edge.gateway import FleetGateway

logger = logging.getLogger("app.edge")


def build_bus() -> MessageBus:
    if settings.edge_transport == "mqtt":
        from dqh.svc_core.messaging.transports.mqtt import MqttMessageBus

        return MqttMessageBus(settings.mqtt)
    return InMemoryMessageBus()


class EdgePlane:
    """Owns the bus + gateway lifecycle."""

    def __init__(self) -> None:
        self.bus: MessageBus = build_bus()
        self.gateway = FleetGateway(self.bus)

    async def start(self) -> None:
        await self.bus.connect()
        await self.gateway.start()

    async def stop(self) -> None:
        await self.gateway.stop()
        await self.bus.aclose()


__all__ = ["EdgePlane", "build_bus"]

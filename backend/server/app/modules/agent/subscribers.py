"""Agent's reactions to events.

Every :class:`HeartbeatRecorded` is relayed to the browser telemetry channel
(see :mod:`app.modules.agent.telemetry_relay`).
"""

from __future__ import annotations

from app.core.events import event_bus
from app.modules.agent import telemetry_relay
from app.modules.agent.event import HeartbeatRecorded


class AgentSubscribers:
    def register(self) -> None:
        event_bus.subscribe(HeartbeatRecorded, telemetry_relay.on_heartbeat)


def register() -> None:
    AgentSubscribers().register()


__all__ = ["AgentSubscribers", "register"]

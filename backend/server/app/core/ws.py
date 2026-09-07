"""Process-wide WebSocket hub — browser dashboards subscribe here for live domain events.

Mirrors :mod:`app.core.events` (the in-process ``event_bus``): modules publish after
their own commit, this module only fans messages out to connected sockets. Swap the
transport later (e.g. Redis pub/sub so pushes work across multiple server replicas)
without touching any publish call site — see ``dqh.svc_core.messaging.MessageBus``.
"""

from __future__ import annotations

from dqh.svc_core.transports.websocket.hub import WebSocketMessageBus

ws_hub = WebSocketMessageBus()

__all__ = ["ws_hub"]

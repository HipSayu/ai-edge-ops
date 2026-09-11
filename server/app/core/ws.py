"""Process-wide WebSocket hub — browser dashboards subscribe here for live domain events.

Mirrors :mod:`app.core.events` (the in-process ``event_bus``): modules publish after
their own commit, this module only fans messages out to connected sockets. The
transport is chosen by ``REALTIME_TRANSPORT`` (``memory`` | ``redis``) — see
:func:`app.core.messaging.build_realtime_bus`; publish call sites never change.
"""

from __future__ import annotations

from app.core.messaging import build_realtime_bus

ws_hub = build_realtime_bus()

__all__ = ["ws_hub"]

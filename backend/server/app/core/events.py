"""The process-wide domain event bus instance.

The :class:`EventBus` implementation lives in ``dqh.svc_core.events``; this module
just owns the single shared instance every module publishes to and subscribes on.
"""

from __future__ import annotations

from dqh.svc_core.events import EventBus

event_bus = EventBus()

__all__ = ["EventBus", "event_bus"]

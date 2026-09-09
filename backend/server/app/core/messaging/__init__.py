"""Realtime fan-out bus wiring — see :class:`RealtimeBusFactory`."""

from __future__ import annotations

from dqh.svc_core.contracts.messaging import MessageBus

from app.core.messaging.realtime_bus_factory import RealtimeBusFactory


def build_realtime_bus() -> MessageBus:
    return RealtimeBusFactory().build()


__all__ = ["RealtimeBusFactory", "build_realtime_bus"]

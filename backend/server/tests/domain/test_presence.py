from __future__ import annotations

import datetime as dt

from app.domain.presence import PresenceRegistry, PresenceStatus


class _Clock:
    def __init__(self) -> None:
        self.now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

    def __call__(self) -> dt.datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += dt.timedelta(seconds=seconds)


def test_first_heartbeat_emits_online():
    reg = PresenceRegistry(stale_after=45, offline_after=90, clock=_Clock())
    event = reg.mark_seen("dev-1")
    assert event is not None
    assert event.previous is None
    assert event.current is PresenceStatus.ONLINE


def test_transitions_online_stale_offline():
    clock = _Clock()
    reg = PresenceRegistry(stale_after=45, offline_after=90, clock=clock)
    reg.mark_seen("dev-1")
    clock.advance(50)
    events = reg.evaluate()
    assert [(e.previous, e.current) for e in events] == [(PresenceStatus.ONLINE, PresenceStatus.STALE)]
    clock.advance(50)
    events = reg.evaluate()
    assert events[0].current is PresenceStatus.OFFLINE
    event = reg.mark_seen("dev-1")
    assert event.current is PresenceStatus.ONLINE


def test_mark_offline_is_immediate():
    reg = PresenceRegistry(clock=_Clock())
    reg.mark_seen("dev-1")
    event = reg.mark_offline("dev-1")
    assert event.current is PresenceStatus.OFFLINE
    assert reg.status("dev-1") is PresenceStatus.OFFLINE


def test_snapshot():
    reg = PresenceRegistry(clock=_Clock())
    reg.mark_seen("a")
    reg.mark_seen("b")
    snap = {s.endpoint_id: s.status for s in reg.snapshot()}
    assert snap == {"a": PresenceStatus.ONLINE, "b": PresenceStatus.ONLINE}
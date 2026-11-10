"""Sends events from a thread of its own, from an outbox on disk: a slow or absent broker never holds up the detector, and
an event leaves the outbox only when the broker has acknowledged it."""

import logging
import threading
import time

from edge.application.ports import ConfirmedPublisher, EventOutbox
from edge.domain.event import ViolationEvent

log = logging.getLogger("edge.publisher")


class DurablePublisher:
    """publish() only writes to the outbox. The sender thread takes the oldest event, delivers it and removes it once
    acknowledged; when it cannot, it waits (0.5 s, doubling to 10 s) and tries the same event again, so order is kept.
    A restart picks up whatever the outbox still holds. After an unacknowledged send the event may still arrive, so it can
    be delivered twice: the receiver drops the repeat by event_id."""

    def __init__(
        self, outbox: EventOutbox, target: ConfirmedPublisher, retry_min: float = 0.5, retry_max: float = 10.0,
    ) -> None:
        self._outbox, self._target = outbox, target
        self._retry_min, self._retry_max = retry_min, retry_max
        self._wake = threading.Event()  # an event was added
        self._stopping = threading.Event()
        self._thread: threading.Thread | None = None
        self.dropped = 0  # events pushed out of a full outbox

    def start(self) -> None:
        self._thread = threading.Thread(target=self._send_loop, name="publisher", daemon=True)
        self._thread.start()

    def stop(self, drain_timeout: float = 5.0) -> None:
        """Gives the sender a moment to empty the outbox, then ends the thread. What is left stays on disk for the next start."""
        deadline = time.monotonic() + drain_timeout
        while self._thread is not None and self._outbox.pending() and time.monotonic() < deadline:
            time.sleep(0.02)
        self._stopping.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=15)

    def publish(self, event: ViolationEvent) -> None:
        self.dropped += self._outbox.add(event)
        self._wake.set()

    def _send_loop(self) -> None:
        delay = self._retry_min
        while not self._stopping.is_set():
            event = self._outbox.oldest()
            if event is None:
                self._wake.wait(1.0)
                self._wake.clear()  # after the wait, before the next look: an event added since is found by that look
                continue
            try:
                sent = self._target.deliver(event)
            except Exception:  # one bad event must not end the sender
                log.exception("event %s not sent", event.event_id)
                sent = False
            if sent:
                self._outbox.remove(event.event_id)
                delay = self._retry_min
            else:
                self._stopping.wait(delay)
                delay = min(delay * 2, self._retry_max)

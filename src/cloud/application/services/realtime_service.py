import asyncio
import logging
from typing import Any

from hopquangdo.messaging import Message, TopicMatcher

logger = logging.getLogger(__name__)


class RealtimeSubscription:
    """One connected client: its topic filters and a bounded outbound queue."""

    def __init__(self, filters: set[str], queue_size: int) -> None:
        self.filters = filters
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=queue_size)
        self.dropped = 0

    def wants(self, topic: str) -> bool:
        return any(TopicMatcher.matches(f, topic) for f in self.filters)

    def offer(self, item: dict[str, Any]) -> None:
        if self.queue.full():
            self.queue.get_nowait()  # slow client: drop oldest, keep latest
            self.dropped += 1
        self.queue.put_nowait(item)


class RealtimeService:
    """Fans out edge MQTT messages (state/telemetry/events) to realtime subscribers in this API process."""

    def __init__(self, queue_size: int = 256) -> None:
        self._subs: set[RealtimeSubscription] = set()
        self._queue_size = queue_size

    def subscribe(self, filters: set[str]) -> RealtimeSubscription:
        sub = RealtimeSubscription(filters, self._queue_size)
        self._subs.add(sub)
        return sub

    def unsubscribe(self, sub: RealtimeSubscription) -> None:
        self._subs.discard(sub)

    @property
    def subscriber_count(self) -> int:
        return len(self._subs)

    async def publish(self, message: Message) -> None:
        if not self._subs:
            return
        item = {
            "topic": message.topic,
            "payload": message.payload if isinstance(message.payload, dict) else message.payload_as_str(),
            "timestamp": message.timestamp.isoformat(),
        }
        for sub in list(self._subs):
            if sub.wants(message.topic):
                sub.offer(item)

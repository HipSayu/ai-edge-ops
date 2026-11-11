"""The SeenEvents contract of edge_link over Redis: several cloud instances, or one that restarted, agree on which edge
events were already taken."""

from redis import Redis


class RedisSeenEvents:
    def __init__(self, client: Redis, ttl_sec: int, prefix: str = "cloud:edge-event:") -> None:
        self._client = client
        self._ttl = ttl_sec
        self._prefix = prefix

    def claim(self, event_id: str) -> bool:
        # SET NX is atomic: of two instances taking the same event at once, exactly one gets True
        return bool(self._client.set(self._prefix + event_id, 1, nx=True, ex=self._ttl))

    def release(self, event_id: str) -> None:
        self._client.delete(self._prefix + event_id)

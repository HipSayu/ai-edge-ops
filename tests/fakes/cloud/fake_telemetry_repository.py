from collections import defaultdict, deque
from typing import Any


class FakeTelemetryRepository:
    def __init__(self, history_size: int = 720) -> None:
        self._latest: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        self._history: dict[tuple[str, str], deque] = defaultdict(lambda: deque(maxlen=history_size))

    async def record(self, node_id: str, kind: str, key: str, sample: dict[str, Any]) -> None:
        self._latest[node_id][key] = sample
        self._history[(node_id, kind)].appendleft(sample)

    async def latest(self, node_id: str) -> dict[str, dict[str, Any]]:
        return dict(self._latest.get(node_id, {}))

    async def history(self, node_id: str, kind: str, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._history.get((node_id, kind), []))[:limit]

    async def ping(self) -> bool:
        return True

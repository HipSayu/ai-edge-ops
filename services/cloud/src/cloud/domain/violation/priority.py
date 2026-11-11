"""Grid ranking: which cameras the wall shows and in what order. Pure logic, no I/O."""

from dataclasses import dataclass

VIOLATION_WEIGHT = 3.0
PERSON_WEIGHT = 1.0
EMA_KEEP = 0.7  # smoothing: share of the previous score kept on each refresh
SWAP_RATIO = 1.5  # a camera outside the grid must beat the weakest inside by this factor...
SWAP_OFFSET = 1.0  # ...plus this margin
MIN_TENURE_SEC = 10.0  # a camera stays on the grid at least this long before it can be swapped out


@dataclass(frozen=True)
class CameraLoad:
    camera_id: int
    person_count: int
    recent_violations: int  # violations in the last minute


def raw_score(load: CameraLoad) -> float:
    return VIOLATION_WEIGHT * load.recent_violations + PERSON_WEIGHT * load.person_count


class GridRanker:
    """Keeps the visible set between refreshes, so the wall does not flicker."""

    def __init__(self, size: int) -> None:
        self._size = size
        self._scores: dict[int, float] = {}
        self._visible: list[int] = []
        self._since: dict[int, float] = {}  # when each visible camera got on the grid

    def score(self, camera_id: int) -> float:
        return self._scores.get(camera_id, 0.0)

    def rank(self, loads: list[CameraLoad], now: float) -> list[int]:
        current = {load.camera_id for load in loads}
        for load in loads:
            raw = raw_score(load)
            previous = self._scores.get(load.camera_id, raw)
            self._scores[load.camera_id] = EMA_KEEP * previous + (1 - EMA_KEEP) * raw
        self._scores = {c: s for c, s in self._scores.items() if c in current}
        self._visible = [c for c in self._visible if c in current]
        self._since = {c: t for c, t in self._since.items() if c in current}

        ranked = sorted(current, key=lambda c: (-self._scores[c], c))
        for camera_id in ranked:
            if len(self._visible) >= self._size:
                break
            if camera_id not in self._visible:
                self._visible.append(camera_id)
                self._since[camera_id] = now

        for camera_id in ranked:
            if camera_id in self._visible:
                continue
            weakest = min(self._visible, key=lambda c: self._scores[c])
            beats = self._scores[camera_id] > SWAP_RATIO * self._scores[weakest] + SWAP_OFFSET
            settled = now - self._since[weakest] >= MIN_TENURE_SEC
            if beats and settled:
                self._visible.remove(weakest)
                del self._since[weakest]
                self._visible.append(camera_id)
                self._since[camera_id] = now

        return sorted(self._visible, key=lambda c: (-self._scores[c], c))

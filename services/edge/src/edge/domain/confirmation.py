class Confirmation:
    """A violation counts only once it has been seen `min_frames` times (per key), so one frame the detector got wrong
    raises no alarm. A key not seen for `forget_after` seconds starts over, which also keeps the table from growing
    with every track the tracker ever issued."""

    def __init__(self, min_frames: int = 1, forget_after: float = 10.0) -> None:
        self._min_frames = min_frames
        self._forget_after = forget_after
        self._seen: dict[object, tuple[int, float]] = {}  # key -> (times seen, when last)

    def confirm(self, key: object, now: float) -> bool:
        """Records one sighting of `key`; True when it has been seen often enough."""
        count, last = self._seen.get(key, (0, now))
        if now - last > self._forget_after:
            count = 0
        count += 1
        self._seen = {k: v for k, v in self._seen.items() if now - v[1] <= self._forget_after}
        self._seen[key] = (count, now)
        return count >= self._min_frames

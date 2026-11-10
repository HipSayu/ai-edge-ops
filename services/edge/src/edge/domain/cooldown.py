class Cooldown:
    """Lets the same kind of violation through at most once per `seconds` (per key), so one person standing
    without a helmet does not flood the cloud with an event per frame."""

    def __init__(self, seconds: float) -> None:
        self._seconds = seconds
        self._last: dict[str, float] = {}

    def allow(self, key: str, now: float) -> bool:
        last = self._last.get(key)
        if last is not None and now - last < self._seconds:
            return False
        self._last = {k: t for k, t in self._last.items() if now - t < self._seconds}  # a key past its cooldown is as good as new
        self._last[key] = now
        return True

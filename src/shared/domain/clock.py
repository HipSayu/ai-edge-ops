from datetime import datetime, timezone


class Clock:
    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)

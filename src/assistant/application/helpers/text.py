import json
from typing import Any


def to_text(value: Any) -> str:
    """A tool result / payload as text: strings as-is, anything else as JSON (non-ASCII kept)."""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)


def truncate(text: str, limit: int) -> str:
    return f"{text[:limit]}…" if len(text) > limit else text

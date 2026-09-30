import asyncio
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


async def run_every(interval_sec: float, fn: Callable[[], Awaitable[object]], *, immediately: bool = False) -> None:
    """Calls `fn` every `interval_sec` until cancelled. A failing call is logged and the loop goes on."""
    if not immediately:
        await asyncio.sleep(interval_sec)
    while True:
        try:
            await fn()
        except Exception:
            logger.exception("Periodic task %s failed", getattr(fn, "__qualname__", fn))
        await asyncio.sleep(interval_sec)

"""Fast metric pump — samples host metrics on a short interval and flushes
them to the control plane as ``TelemetryPayload`` batches.

Separate from :class:`edge_agent.network.link.EdgeLink`'s 15s health
heartbeat: this is the stream that drives live dashboard gauges, so it runs
at ~1s and the server fans it out over WebSocket without persisting every
sample.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections import deque
from collections.abc import Awaitable, Callable

import edge_protocol as p

from edge_agent.core.config import TelemetryConfig
from edge_agent.core.hardware import Hardware
from edge_agent.utils.metrics import collect_metrics

logger = logging.getLogger("edge_agent.services.telemetry")

TelemetrySink = Callable[[p.TelemetryPayload], Awaitable[None]]


class TelemetryPump:
    def __init__(
        self,
        config: TelemetryConfig,
        *,
        sink: TelemetrySink,
        hardware: Hardware | None = None,
        collector: Callable[..., p.HeartbeatPayload] = collect_metrics,
    ) -> None:
        self._config = config
        self._sink = sink
        self._hw = hardware
        self._collect = collector
        # cap the buffer so a stalled uplink can't grow it without bound
        self._buffer: deque[p.HeartbeatPayload] = deque(maxlen=120)
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if not self._config.enabled or self._task is not None:
            return
        self._task = asyncio.create_task(self._run(), name="telemetry-pump")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _run(self) -> None:
        sample_every = max(self._config.sample_interval_s, 0.02)
        flush_every = max(self._config.flush_interval_s, sample_every)
        since_flush = 0.0
        while True:
            try:
                self._buffer.append(self._collect(hardware=self._hw))
            except Exception:  # noqa: BLE001 - a bad sample must not kill the pump
                logger.exception("telemetry sample failed")
            await asyncio.sleep(sample_every)
            since_flush += sample_every
            if since_flush >= flush_every and self._buffer:
                since_flush = 0.0
                await self._flush()

    async def _flush(self) -> None:
        batch = list(self._buffer)
        self._buffer.clear()
        try:
            await self._sink(p.TelemetryPayload(samples=batch))
        except Exception:  # noqa: BLE001 - drop the batch, keep sampling
            logger.warning("telemetry flush failed; dropping %d samples", len(batch))


__all__ = ["TelemetryPump"]

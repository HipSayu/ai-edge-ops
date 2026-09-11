from __future__ import annotations

import asyncio

import edge_protocol as p

from edge_agent.core.config import TelemetryConfig
from edge_agent.services.telemetry import TelemetryPump


def _sample(**kw) -> p.HeartbeatPayload:
    return p.HeartbeatPayload(cpu_percent=12.0, mem_percent=30.0, **kw)


async def test_pump_flushes_batches_to_sink():
    flushed: list[p.TelemetryPayload] = []

    async def sink(payload: p.TelemetryPayload) -> None:
        flushed.append(payload)

    pump = TelemetryPump(
        TelemetryConfig(sample_interval_s=0.05, flush_interval_s=0.1),
        sink=sink,
        collector=lambda **_: _sample(),
    )
    pump.start()
    await asyncio.sleep(0.6)
    await pump.stop()

    assert flushed, "expected at least one telemetry batch"
    assert all(isinstance(s, p.HeartbeatPayload) for s in flushed[0].samples)
    assert sum(len(b.samples) for b in flushed) >= 3


async def test_pump_disabled_never_starts():
    called = False

    async def sink(_payload: p.TelemetryPayload) -> None:
        nonlocal called
        called = True

    pump = TelemetryPump(
        TelemetryConfig(enabled=False), sink=sink, collector=lambda **_: _sample()
    )
    pump.start()
    await asyncio.sleep(0.1)
    await pump.stop()
    assert called is False


async def test_pump_survives_a_bad_sample():
    flushed: list[p.TelemetryPayload] = []
    calls = {"n": 0}

    def collector(**_):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("sensor glitch")
        return _sample()

    async def sink(payload: p.TelemetryPayload) -> None:
        flushed.append(payload)

    pump = TelemetryPump(
        TelemetryConfig(sample_interval_s=0.05, flush_interval_s=0.1),
        sink=sink,
        collector=collector,
    )
    pump.start()
    await asyncio.sleep(0.6)
    await pump.stop()

    assert flushed, "pump should keep going after one failed sample"

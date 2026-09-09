from __future__ import annotations

import asyncio

import pytest
from dqh.svc_core.messaging import Envelope

from app.core.messaging.redis_bus import RedisPubSubMessageBus, _to_redis_pattern


def test_mqtt_filter_to_redis_glob():
    assert _to_redis_pattern("telemetry/3") == "telemetry/3"
    assert _to_redis_pattern("telemetry/+") == "telemetry/*"
    assert _to_redis_pattern("telemetry/#") == "telemetry/*"
    assert _to_redis_pattern("a/+/c/#") == "a/*/c/*"


@pytest.fixture
async def bus():
    fakeredis = pytest.importorskip("fakeredis")
    server = fakeredis.FakeServer()

    class _Bus(RedisPubSubMessageBus):
        async def connect(self) -> None:  # swap the real client for the fake
            import fakeredis.aioredis as far

            self._redis = far.FakeRedis(server=server)
            self._pubsub = self._redis.pubsub(ignore_subscribe_messages=True)
            self._reader = asyncio.create_task(self._read_loop())

    b = _Bus("redis://fake")
    await b.connect()
    yield b
    await b.aclose()


async def _wait(predicate, timeout=2.0):
    async def _loop():
        while not predicate():
            await asyncio.sleep(0.02)

    await asyncio.wait_for(_loop(), timeout)


async def test_wildcard_delivery_and_isolation(bus):
    got: list[Envelope] = []

    async def handler(env: Envelope) -> None:
        got.append(env)

    sub = await bus.subscribe("telemetry/#", handler)
    await asyncio.sleep(0.1)  # let psubscribe land

    await bus.publish("telemetry/7", Envelope(type="telemetry.device", source="s", payload={"n": 1}))
    await bus.publish("logs/7", Envelope(type="log", source="s", payload={"n": 2}))

    await _wait(lambda: len(got) >= 1)
    assert [e.payload["n"] for e in got] == [1]  # logs/7 filtered out

    await sub.unsubscribe()
    await bus.publish("telemetry/7", Envelope(type="telemetry.device", source="s", payload={"n": 3}))
    await asyncio.sleep(0.2)
    assert [e.payload["n"] for e in got] == [1]  # nothing after unsubscribe

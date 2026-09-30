import fakeredis

from src.assistant.infrastructure.messaging.redis_stream_queue import RedisStreamQueue


async def test_frames_reach_exactly_one_consumer():
    redis = fakeredis.FakeAsyncRedis()
    producer = RedisStreamQueue(redis, idle_timeout_sec=1)
    consumer = RedisStreamQueue(redis, idle_timeout_sec=1)  # another replica, same Redis

    await producer.open("s1")
    await producer.put("s1", "event: token\ndata: a\n\n")
    await producer.put("s1", "event: done\ndata: b\n\n")
    await producer.close("s1")

    frames = await consumer.subscribe("s1")
    assert frames is not None
    assert [f async for f in frames] == ["event: token\ndata: a\n\n", "event: done\ndata: b\n\n"]

    assert await consumer.subscribe("s1") is None  # already claimed
    assert await consumer.subscribe("unknown") is None
    assert await redis.exists("chat:stream:s1") == 0  # drained stream is removed

"""The Redis-backed SeenEvents, against a real Redis: set CLOUD_TEST_REDIS (e.g. redis://:password@127.0.0.1:6379/0)."""

import os
import uuid

import pytest
from redis import Redis

from cloud.infrastructure.messaging.redis_seen import RedisSeenEvents
import time

URL = os.environ.get("CLOUD_TEST_REDIS")
pytestmark = pytest.mark.skipif(not URL, reason="CLOUD_TEST_REDIS is not set")


@pytest.fixture
def seen():
    client = Redis.from_url(URL)
    yield RedisSeenEvents(client, ttl_sec=30, prefix=f"test:{uuid.uuid4().hex}:")
    client.close()


def test_the_first_claim_wins_and_the_rest_are_refused(seen):
    assert seen.claim("e1")
    assert not seen.claim("e1")
    assert seen.claim("e2")


def test_a_released_event_can_be_claimed_again(seen):
    assert seen.claim("e1")
    seen.release("e1")
    assert seen.claim("e1")


def test_two_instances_on_the_same_store_agree():
    client = Redis.from_url(URL)
    prefix = f"test:{uuid.uuid4().hex}:"
    a, b = RedisSeenEvents(client, 30, prefix), RedisSeenEvents(Redis.from_url(URL), 30, prefix)
    assert a.claim("e1") and not b.claim("e1")


def test_the_claim_expires(seen):
    client = Redis.from_url(URL)
    short = RedisSeenEvents(client, ttl_sec=1, prefix=f"test:{uuid.uuid4().hex}:")
    assert short.claim("e1")
    time.sleep(1.5)
    assert short.claim("e1")

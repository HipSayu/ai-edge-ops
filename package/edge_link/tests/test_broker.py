"""The link through a real MQTT broker. Runs only when EDGE_LINK_TEST_BROKER=host:port points at one that allows
anonymous clients (CI starts mosquitto; locally: docker run --rm -p 1883:1883 eclipse-mosquitto:2 with such a config)."""

import os
import threading
import uuid

import pytest

from edge_link import EventPublisher, EventSubscriber, ViolationMessage

BROKER = os.environ.get("EDGE_LINK_TEST_BROKER")
pytestmark = pytest.mark.skipif(not BROKER, reason="EDGE_LINK_TEST_BROKER is not set")


def test_event_travels_from_publisher_to_subscriber():
    host, port = BROKER.split(":")
    node = f"n-{uuid.uuid4().hex[:8]}"
    got, arrived = [], threading.Event()

    def handler(event: ViolationMessage) -> None:
        got.append(event)
        arrived.set()

    subscriber = EventSubscriber(host, int(port), handler, client_id=f"test-sub-{node}")
    publisher = EventPublisher(node, host, int(port))
    subscriber.start()
    publisher.start()
    try:
        message = ViolationMessage(event_id=uuid.uuid4().hex, node_id=node, camera_id=7, violation_type="no_helmet",
                                   confidence=0.9, occurred_at="2026-10-21T01:00:00+00:00", video_ts_sec=1.5,
                                   snapshot_jpeg=b"\xff\xd8jpeg")
        # The subscription may not be in place yet: send until it is heard (redeliveries are dropped by event_id)
        for _ in range(20):
            publisher.send(message)
            if arrived.wait(0.5):
                break
        assert got and got[0].camera_id == 7 and got[0].snapshot_jpeg == message.snapshot_jpeg
    finally:
        publisher.stop()
        subscriber.stop()

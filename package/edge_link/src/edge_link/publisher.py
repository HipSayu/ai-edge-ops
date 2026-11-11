"""The edge side of the link: connects to the broker and sends events.

The client reconnects by itself and keeps messages sent with send() while the broker is away (in memory), so a short
outage loses nothing; a restart of the sender does. deliver() is for a caller that keeps its own copy (an outbox) until
the broker has acknowledged the message."""

from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt

from edge_link.messages import DetectionsMessage, ViolationMessage, ZonesMessage
from edge_link.topics import (
    OFFLINE, ONLINE, QOS, QOS_DETECTIONS, ZONES_QOS, detections_topic, events_topic, status_topic, zones_topic,
)


def default_client(client_id: str) -> Any:
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)


class EventPublisher:
    def __init__(
        self, node_id: str, host: str, port: int = 1883, username: str | None = None, password: str | None = None,
        client_factory: Callable[[str], Any] = default_client, tls_ca: str | None = None,
    ) -> None:
        self._node_id, self._host, self._port = node_id, host, port
        self._client = client_factory(f"edge-{node_id}")
        if username:
            self._client.username_pw_set(username, password)
        if tls_ca:
            self._client.tls_set(ca_certs=tls_ca)  # checks the broker's certificate and its host name
        self._client.will_set(status_topic(node_id), OFFLINE, qos=QOS, retain=True)  # what the broker says if we vanish
        self._client.on_connect = self._on_connect

    def _on_connect(self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        client.publish(status_topic(self._node_id), ONLINE, qos=QOS, retain=True)  # again after every reconnect

    def start(self) -> None:
        self._client.connect_async(self._host, self._port)  # does not fail when the broker is down: it retries
        self._client.loop_start()

    def stop(self) -> None:
        self._client.publish(status_topic(self._node_id), OFFLINE, qos=QOS, retain=True)
        self._client.disconnect()
        self._client.loop_stop()

    def send(self, message: ViolationMessage) -> None:
        self._client.publish(events_topic(message.node_id, message.camera_id), message.to_json(), qos=QOS)

    def deliver(self, message: ViolationMessage, timeout: float = 10.0) -> bool:
        """Sends one event and waits for the broker to acknowledge it (QoS 1). False when the link is down or the broker
        did not answer in time. Nothing is handed to the client while the link is down, so the caller still owns the event
        and tries again; after a timeout the client may still deliver it later, which the receiver's event_id check absorbs."""
        if not self._client.is_connected():
            return False
        info = self._client.publish(events_topic(message.node_id, message.camera_id), message.to_json(), qos=QOS)
        try:
            info.wait_for_publish(timeout)
        except (ValueError, RuntimeError):  # paho: not queued (queue full) or not published
            return False
        return bool(info.is_published())

    def send_detections(self, message: DetectionsMessage) -> None:
        self._client.publish(detections_topic(message.node_id, message.camera_id), message.to_json(), qos=QOS_DETECTIONS)


class ZonesPublisher:
    """The cloud side of the zones: sends the zones of a camera, retained, so a node gets them whenever it connects."""

    def __init__(
        self, host: str, port: int = 1883, username: str | None = None, password: str | None = None,
        client_factory: Callable[[str], Any] = default_client, client_id: str = "cloud-zones", tls_ca: str | None = None,
    ) -> None:
        self._host, self._port = host, port
        self._client = client_factory(client_id)
        if username:
            self._client.username_pw_set(username, password)
        if tls_ca:
            self._client.tls_set(ca_certs=tls_ca)

    def start(self) -> None:
        self._client.connect_async(self._host, self._port)  # keeps retrying when the broker is down
        self._client.loop_start()

    def stop(self) -> None:
        self._client.disconnect()
        self._client.loop_stop()

    def publish(self, message: ZonesMessage) -> bool:
        """Queues the zones of one camera, retained. False when the client could not take it."""
        try:
            info = self._client.publish(zones_topic(message.camera_id), message.to_json(), qos=ZONES_QOS, retain=True)
        except (ValueError, RuntimeError):
            return False
        return getattr(info, "rc", 0) == 0

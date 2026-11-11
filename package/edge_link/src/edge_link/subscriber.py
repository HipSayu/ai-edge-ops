"""The cloud side of the link: connects to the broker and hands each event to a handler, once."""

import logging
from collections.abc import Callable
from typing import Any

from edge_link.messages import DetectionsMessage, ViolationMessage, ZonesMessage
from edge_link.publisher import default_client
from edge_link.seen import MemorySeen, SeenEvents
from edge_link.topics import DETECTIONS_FILTER, EVENTS_FILTER, QOS, QOS_DETECTIONS, ZONES_QOS, zones_topic

log = logging.getLogger("edge_link")


class EventSubscriber:
    def __init__(
        self, host: str, port: int, handler: Callable[[ViolationMessage], None],
        username: str | None = None, password: str | None = None,
        client_factory: Callable[[str], Any] = default_client, client_id: str = "cloud-events",
        tls_ca: str | None = None, seen: SeenEvents | None = None,
        on_detections: Callable[[DetectionsMessage], None] | None = None,
    ) -> None:
        self._host, self._port, self._handler = host, port, handler
        self._on_detections = on_detections  # None: the boxes are not listened to
        self._seen = seen or MemorySeen()
        self._client = client_factory(client_id)
        if username:
            self._client.username_pw_set(username, password)
        if tls_ca:
            self._client.tls_set(ca_certs=tls_ca)  # checks the broker's certificate and its host name
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def start(self) -> None:
        self._client.connect_async(self._host, self._port)  # keeps retrying when the broker is down
        self._client.loop_start()

    def stop(self) -> None:
        self._client.disconnect()
        self._client.loop_stop()

    def _on_connect(self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        client.subscribe(EVENTS_FILTER, qos=QOS)  # again after every reconnect
        if self._on_detections:
            client.subscribe(DETECTIONS_FILTER, qos=QOS_DETECTIONS)

    def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
        if str(getattr(message, "topic", "")).endswith("/detections"):
            self.handle_detections(message.payload)
        else:
            self.handle(message.payload)

    def handle_detections(self, payload: bytes | str) -> bool:
        """Passes one set of boxes to its handler. False when it was malformed or nobody listens."""
        if not self._on_detections:
            return False
        try:
            message = DetectionsMessage.parse(payload)
        except ValueError:
            log.debug("dropped a malformed detections message")
            return False
        self._on_detections(message)
        return True

    def handle(self, payload: bytes | str) -> bool:
        """Passes one message to the handler. False when it was dropped: malformed, seen before, or the handler failed
        (then the same event may be tried again if the broker redelivers it)."""
        try:
            event = ViolationMessage.parse(payload)
        except ValueError:
            log.warning("dropped a malformed event message")
            return False
        if not self._seen.claim(event.event_id):
            return False
        try:
            self._handler(event)
        except Exception:  # keep listening whatever one event does
            self._seen.release(event.event_id)
            log.exception("could not handle event %s", event.event_id)
            return False
        return True


class ZonesSubscriber:
    """The edge side of the zones: listens for the zones of the cameras this node runs and hands each message to a
    handler. The broker keeps the last message of every topic (retained), so the handler is called as soon as the link is
    up, also after a restart."""

    def __init__(
        self, camera_ids: list[int], host: str, port: int, handler: Callable[[ZonesMessage], None],
        username: str | None = None, password: str | None = None,
        client_factory: Callable[[str], Any] = default_client, client_id: str = "edge-zones", tls_ca: str | None = None,
    ) -> None:
        self._camera_ids = set(camera_ids)
        self._host, self._port, self._handler = host, port, handler
        self._client = client_factory(client_id)
        if username:
            self._client.username_pw_set(username, password)
        if tls_ca:
            self._client.tls_set(ca_certs=tls_ca)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def start(self) -> None:
        self._client.connect_async(self._host, self._port)
        self._client.loop_start()

    def stop(self) -> None:
        self._client.disconnect()
        self._client.loop_stop()

    def _on_connect(self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        for camera_id in sorted(self._camera_ids):  # again after every reconnect
            client.subscribe(zones_topic(camera_id), qos=ZONES_QOS)

    def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
        self.handle(message.payload)

    def handle(self, payload: bytes | str) -> bool:
        """Passes the zones of one camera to the handler. False when the message was malformed, for a camera this node does
        not run, or the handler failed."""
        try:
            message = ZonesMessage.parse(payload)
        except ValueError:
            log.warning("dropped a malformed zones message")
            return False
        if message.camera_id not in self._camera_ids:
            return False
        try:
            self._handler(message)
        except Exception:
            log.exception("could not apply the zones of camera %s", message.camera_id)
            return False
        return True

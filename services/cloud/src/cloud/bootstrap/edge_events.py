"""Events from the edge runtimes: each one is filed as a violation."""

import logging

from collections.abc import Callable

from edge_link import DetectionsMessage, EventSubscriber, SeenEvents, ViolationMessage

from cloud.bootstrap.settings import Settings
from cloud.application.usecases.violation_recorder import EventSink
from cloud.domain.violation.violations import EVENT_TYPES

log = logging.getLogger("ppe.edge")


def build_edge_events(
    settings: Settings, on_event: EventSink, seen: SeenEvents | None = None,
    on_detections: Callable[[DetectionsMessage], None] | None = None,
) -> EventSubscriber | None:
    """The subscriber, or None when no broker is configured. `seen` decides which redeliveries are dropped."""
    if not settings.mqtt_host:
        return None

    def file_event(event: ViolationMessage) -> None:
        if event.violation_type not in EVENT_TYPES:
            log.warning("dropped an edge event of unknown type %r", event.violation_type)
            return
        on_event(event.camera_id, event.violation_type, event.confidence, event.video_ts_sec, event.snapshot_jpeg)

    return EventSubscriber(
        settings.mqtt_host, settings.mqtt_port, file_event, settings.mqtt_username, settings.mqtt_password,
        client_id="cloud-edge-events", tls_ca=str(settings.mqtt_tls_ca) if settings.mqtt_tls_ca else None, seen=seen,
        on_detections=on_detections,
    )

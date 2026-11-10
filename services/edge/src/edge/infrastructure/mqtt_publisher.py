"""The EventPublisher port over MQTT: turns an event into the shared message and sends it through the edge_link."""

from collections.abc import Callable
from typing import Any

from edge_link import DetectionBox, DetectionsMessage, EventPublisher, ViolationMessage
from edge_link.publisher import default_client

from edge.domain.detection import Detection
from edge.domain.event import ViolationEvent


def message_of(event: ViolationEvent) -> ViolationMessage:
    return ViolationMessage(
        event_id=event.event_id, node_id=event.node_id, camera_id=event.camera_id,
        violation_type=event.violation_type, confidence=event.confidence, occurred_at=event.occurred_at.isoformat(),
        video_ts_sec=event.video_ts_sec, snapshot_jpeg=event.snapshot_jpeg,
    )


class MqttEventPublisher:
    def __init__(
        self, node_id: str, host: str, port: int = 1883, username: str | None = None, password: str | None = None,
        client_factory: Callable[[str], Any] = default_client, tls_ca: str | None = None,
    ) -> None:
        self._node_id = node_id
        self._link = EventPublisher(node_id, host, port, username, password, client_factory, tls_ca)

    def start(self) -> None:
        self._link.start()

    def stop(self) -> None:
        self._link.stop()

    def publish(self, event: ViolationEvent) -> None:
        self._link.send(message_of(event))

    def deliver(self, event: ViolationEvent) -> bool:
        return self._link.deliver(message_of(event))

    def publish_detections(
        self, camera_id: int, ts_sec: float, width: int, height: int, detections: list[Detection],
        fps: float = 0.0, infer_ms: float = 0.0, dropped: int = 0,
    ) -> None:
        self._link.send_detections(DetectionsMessage(
            node_id=self._node_id, camera_id=camera_id, video_ts_sec=ts_sec, width=width, height=height,
            boxes=tuple(DetectionBox(d.label, d.confidence, d.box, d.track_id) for d in detections),
            fps=fps, infer_ms=infer_ms, dropped=dropped,
        ))

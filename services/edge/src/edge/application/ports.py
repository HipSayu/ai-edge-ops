"""What the edge runtime needs from the outside. Infrastructure implements these; nothing here imports it."""

import threading
from collections.abc import Callable
from typing import Protocol

import numpy as np

from edge.domain.detection import Detection
from edge.domain.event import ViolationEvent


# What the stream hands over for one camera and one detection: which camera, where in the source (0 for a live camera that
# has none), the frame's size in pixels, the detections (already tracked), and a way to get the picture only when it is needed.
DetectionHandler = Callable[[int, float, int, int, "list[Detection]", Callable[[], np.ndarray]], None]


class DetectionStream(Protocol):
    """Everything between the cameras and the detections of one node: reading, decoding, batching, the model and the
    tracker. It calls `handler` once per camera frame it looked at, and keeps going until `stop` is set or it fails."""

    def run(self, handler: DetectionHandler, stop: threading.Event) -> None: ...


class SnapshotRenderer(Protocol):
    def render(self, image: np.ndarray, detections: list[Detection]) -> bytes:
        """The frame with the detections drawn on it, as JPEG."""


class EventPublisher(Protocol):
    def publish(self, event: ViolationEvent) -> None: ...


class ConfirmedPublisher(Protocol):
    def deliver(self, event: ViolationEvent) -> bool:
        """True once the cloud's broker has acknowledged the event; False when it could not be sent now."""


class EventOutbox(Protocol):
    """Events not yet acknowledged, kept on disk so a restart or a long outage does not lose them."""

    def add(self, event: ViolationEvent) -> int:
        """Stores the event. Returns how many older events were dropped to stay within the limit."""

    def oldest(self) -> ViolationEvent | None: ...

    def remove(self, event_id: str) -> None: ...

    def pending(self) -> int: ...


class DetectionPublisher(Protocol):
    """Where every box of a detection goes, for the live overlay. Losing one is fine: the next comes in a moment."""

    def publish_detections(
        self, camera_id: int, ts_sec: float, width: int, height: int, detections: list[Detection],
        fps: float = 0.0, infer_ms: float = 0.0, dropped: int = 0,
    ) -> None: ...


class AlarmSink(Protocol):
    """Where an alarm goes, on the spot (a siren, a speaker, a light). Works without the cloud."""

    def trigger(self, camera_id: int, reason: str) -> None: ...

"""What the edge runtime needs from the outside. Infrastructure implements these; nothing here imports it."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from edge.domain.detection import Detection
from edge.domain.event import ViolationEvent


@dataclass(frozen=True)
class Frame:
    image: np.ndarray
    ts_sec: float  # position in the source (0 for a live camera that has none)


class FrameSource(Protocol):
    def frames(self) -> Iterator[Frame]:
        """Frames at the source's own pace. Ends when the source gives up (or never, for a looping source)."""


class Detector(Protocol):
    def detect(self, image: np.ndarray) -> list[Detection]: ...


class Tracker(Protocol):
    def update(self, detections: list[Detection]) -> list[Detection]:
        """The same detections with the id of the track each one belongs to (None where there is none yet). Keeps
        the tracks of one camera, so every camera has its own."""


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

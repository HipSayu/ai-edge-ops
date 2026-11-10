"""A PPE violation seen by a camera, ready to be sent to the cloud."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class ViolationEvent:
    node_id: str
    camera_id: int
    violation_type: str
    confidence: float
    video_ts_sec: float  # position in the video the frame came from
    snapshot_jpeg: bytes  # the frame with the detections drawn on it
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)  # lets the receiver drop a redelivered message
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


ZONE_INTRUSION = "zone_intrusion"  # the violation_type of someone who walked into a forbidden zone (see domain/zone.py)

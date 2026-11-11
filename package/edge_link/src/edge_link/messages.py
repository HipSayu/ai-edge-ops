"""The messages that travel between the edge runtimes and the cloud. Both sides use these classes, so the wire format
changes in one place."""

import base64
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ViolationMessage:
    event_id: str  # unique per event: QoS 1 may deliver a message twice, the receiver drops repeats by it
    node_id: str
    camera_id: int
    violation_type: str
    confidence: float
    occurred_at: str  # ISO 8601, UTC
    video_ts_sec: float
    snapshot_jpeg: bytes  # the frame with the detections drawn on it

    def to_json(self) -> str:
        return json.dumps({
            "event_id": self.event_id,
            "node_id": self.node_id,
            "camera_id": self.camera_id,
            "violation_type": self.violation_type,
            "confidence": round(self.confidence, 4),
            "occurred_at": self.occurred_at,
            "video_ts_sec": round(self.video_ts_sec, 3),
            "snapshot_jpeg_b64": base64.b64encode(self.snapshot_jpeg).decode("ascii"),
        })

    @classmethod
    def parse(cls, payload: bytes | str) -> "ViolationMessage":
        """Raises ValueError when the payload is not a well-formed message."""
        try:
            body = json.loads(payload)
            return cls(
                event_id=str(body["event_id"]),
                node_id=str(body["node_id"]),
                camera_id=int(body["camera_id"]),
                violation_type=str(body["violation_type"]),
                confidence=float(body["confidence"]),
                occurred_at=str(body["occurred_at"]),
                video_ts_sec=float(body.get("video_ts_sec", 0.0)),
                snapshot_jpeg=base64.b64decode(body["snapshot_jpeg_b64"], validate=True),
            )
        except (KeyError, TypeError, AttributeError) as e:  # ValueError (bad JSON, bad number, bad base64) passes as is
            raise ValueError(f"malformed violation message: {e!r}") from e


@dataclass(frozen=True)
class DetectionBox:
    label: str
    confidence: float
    box: tuple[int, int, int, int]  # x1, y1, x2, y2 in the pixels of the frame
    track_id: int | None = None


@dataclass(frozen=True)
class DetectionsMessage:
    """What one detection found in one frame: all its boxes, with the position of the frame in the camera's timeline."""

    node_id: str
    camera_id: int
    video_ts_sec: float
    width: int  # of the frame the boxes are in
    height: int
    boxes: tuple[DetectionBox, ...]
    fps: float = 0.0  # detections per second this camera is getting on the edge
    infer_ms: float = 0.0  # milliseconds one detection takes there
    dropped: int = 0  # frames the detector had no time for, since the edge started

    def to_json(self) -> str:
        return json.dumps({
            "node_id": self.node_id,
            "camera_id": self.camera_id,
            "ts": round(self.video_ts_sec, 3),
            "fps": round(self.fps, 1),
            "ms": round(self.infer_ms, 1),
            "drop": self.dropped,
            "w": self.width,
            "h": self.height,
            "boxes": [[b.label, round(b.confidence, 3), *b.box, b.track_id] for b in self.boxes],
        }, separators=(",", ":"))

    @classmethod
    def parse(cls, payload: bytes | str) -> "DetectionsMessage":
        """Raises ValueError when the payload is not a well-formed message."""
        try:
            body = json.loads(payload)
            return cls(
                node_id=str(body["node_id"]), camera_id=int(body["camera_id"]), video_ts_sec=float(body["ts"]),
                width=int(body["w"]), height=int(body["h"]),
                boxes=tuple(
                    DetectionBox(str(b[0]), float(b[1]), (int(b[2]), int(b[3]), int(b[4]), int(b[5])),
                                 None if b[6] is None else int(b[6]))
                    for b in body["boxes"]
                ),
                fps=float(body.get("fps", 0.0)), infer_ms=float(body.get("ms", 0.0)), dropped=int(body.get("drop", 0)),
            )
        except (KeyError, TypeError, AttributeError, IndexError) as e:
            raise ValueError(f"malformed detections message: {e!r}") from e


@dataclass(frozen=True)
class ZoneSpec:
    """One forbidden zone: a polygon in the frame, as fractions of its width and height so it does not depend on the
    resolution the edge decodes at."""

    id: int
    name: str
    polygon: tuple[tuple[float, float], ...]  # (x, y) corners, each 0..1
    enabled: bool = True


@dataclass(frozen=True)
class ZonesMessage:
    """All the zones of one camera. A newer message replaces the one before it; an empty one clears the camera."""

    camera_id: int
    zones: tuple[ZoneSpec, ...]

    def to_json(self) -> str:
        return json.dumps({
            "camera_id": self.camera_id,
            "zones": [
                {"id": z.id, "name": z.name, "enabled": z.enabled, "polygon": [[round(x, 5), round(y, 5)] for x, y in z.polygon]}
                for z in self.zones
            ],
        }, separators=(",", ":"))

    @classmethod
    def parse(cls, payload: bytes | str) -> "ZonesMessage":
        """Raises ValueError when the payload is not a well-formed message (a polygon needs 3 corners inside the frame)."""
        try:
            body = json.loads(payload)
            zones = []
            for z in body["zones"]:
                polygon = tuple((float(x), float(y)) for x, y in z["polygon"])
                if len(polygon) < 3 or any(not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0) for x, y in polygon):
                    raise ValueError("a zone needs at least 3 corners, each inside the frame")
                zones.append(ZoneSpec(int(z["id"]), str(z["name"]), polygon, bool(z.get("enabled", True))))
            return cls(int(body["camera_id"]), tuple(zones))
        except (KeyError, TypeError, AttributeError) as e:
            raise ValueError(f"malformed zones message: {e!r}") from e

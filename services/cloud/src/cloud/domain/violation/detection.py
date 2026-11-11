"""What a PPE detector found in a picture, for a one-off test from the dashboard (not a camera feed)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FoundObject:
    label: str  # person, helmet, vest, no_helmet...
    confidence: float
    box: tuple[int, int, int, int]  # x1, y1, x2, y2 in the pixels of the picture


@dataclass(frozen=True)
class DetectionResult:
    objects: tuple[FoundObject, ...]
    annotated_jpeg: bytes  # the picture with the boxes drawn on it

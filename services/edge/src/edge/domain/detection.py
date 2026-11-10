from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    box: tuple[int, int, int, int]  # x1, y1, x2, y2
    track_id: int | None = None  # the same object keeps it across frames; None until a tracker has seen it

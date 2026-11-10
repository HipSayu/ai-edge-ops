"""A zone no one may enter, drawn on a camera's frame."""

from dataclasses import dataclass

_EDGE_TOLERANCE = 1e-9


@dataclass(frozen=True)
class Zone:
    id: int
    camera_id: int
    name: str
    polygon: tuple[tuple[float, float], ...]  # corners as fractions (0..1) of the frame's width and height
    enabled: bool = True

    def contains(self, x: float, y: float) -> bool:
        """Whether the point (a fraction of the frame, like the corners) is inside the polygon. A point on its edge counts as
        inside: when someone stands on the line, the alarm should sound rather than not."""
        inside = False
        n = len(self.polygon)
        for i in range(n):
            x1, y1 = self.polygon[i]
            x2, y2 = self.polygon[(i + 1) % n]
            if _on_segment(x, y, x1, y1, x2, y2):
                return True
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:  # a ray to the right crosses this side
                inside = not inside
        return inside


def _on_segment(x: float, y: float, x1: float, y1: float, x2: float, y2: float) -> bool:
    cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    if abs(cross) > _EDGE_TOLERANCE:
        return False
    return min(x1, x2) - _EDGE_TOLERANCE <= x <= max(x1, x2) + _EDGE_TOLERANCE and min(y1, y2) - _EDGE_TOLERANCE <= y <= max(y1, y2) + _EDGE_TOLERANCE


def foot_point(box: tuple[int, int, int, int], width: int, height: int) -> tuple[float, float]:
    """Where a person stands: the middle of the bottom of their box, as a fraction of the frame. The feet are what touch
    the ground the zone is drawn on; the centre of the box would put a tall person inside a zone they stand in front of."""
    x1, _, x2, y2 = box
    return min(max((x1 + x2) / 2 / width, 0.0), 1.0), min(max(y2 / height, 0.0), 1.0)

"""A forbidden zone: a polygon drawn on a camera's picture. Someone who walks into it sets off the alarm at the edge."""

from dataclasses import dataclass

from shared.errors import Invalid
from shared.text import required_name

MAX_CORNERS = 50
MAX_ZONES_PER_CAMERA = 20


@dataclass(frozen=True)
class Zone:
    name: str
    polygon: tuple[tuple[float, float], ...]  # corners as fractions (0..1) of the picture's width and height
    enabled: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", required_name(self.name, "vùng cấm"))
        if not 3 <= len(self.polygon) <= MAX_CORNERS:
            raise Invalid(f"Một vùng cấm cần từ 3 đến {MAX_CORNERS} góc")
        if any(not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0) for x, y in self.polygon):
            raise Invalid("Các góc của vùng cấm phải nằm trong khung hình")
        if _area(self.polygon) < 1e-4:
            raise Invalid("Vùng cấm quá nhỏ hoặc các góc thẳng hàng")


def _area(polygon: tuple[tuple[float, float], ...]) -> float:
    """The shoelace formula: twice the signed area, halved and made positive."""
    twice = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1], strict=True))
    return abs(twice) / 2

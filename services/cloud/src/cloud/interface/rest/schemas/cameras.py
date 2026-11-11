"""Input for the camera routes."""

from pydantic import BaseModel


class CameraIn(BaseModel):
    name: str
    node_id: int
    zone: str | None = None
    enabled: bool = True


class CameraUpdate(BaseModel):
    # node_id is fixed: moving a camera would move its video folder
    name: str
    zone: str | None = None
    enabled: bool = True


class ZoneIn(BaseModel):
    name: str
    polygon: list[tuple[float, float]]  # corners as fractions (0..1) of the picture's width and height
    enabled: bool = True


class ZonesIn(BaseModel):
    zones: list[ZoneIn]

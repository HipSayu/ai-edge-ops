"""Shapes the use cases hand back for reading. They join several aggregates and are not stored as such."""

from dataclasses import dataclass

from cloud.domain.model.node import Camera, Node


@dataclass(frozen=True)
class CameraRow:
    id: int
    name: str
    zone: str | None
    enabled: bool
    node_id: int
    node_name: str
    cluster_id: int
    cluster_name: str


@dataclass(frozen=True)
class CameraDetail:
    row: CameraRow
    videos: list[str]


@dataclass(frozen=True)
class ClusterSummary:
    id: int
    name: str
    description: str | None
    nodes: int


@dataclass(frozen=True)
class NodeSummary:
    id: int
    name: str
    cluster_id: int
    cluster_name: str
    description: str | None
    ip_address: str | None
    max_cameras: int
    camera_count: int


@dataclass(frozen=True)
class CameraStatus:
    id: int
    name: str
    enabled: bool
    cluster: str
    node: str
    people_now: int
    violations_last_10_min: int
    videos: list[str]


@dataclass(frozen=True)
class UserSummary:
    id: int
    username: str
    full_name: str
    role: str
    active: bool
    clusters: list[str]


@dataclass(frozen=True)
class GridItem:
    camera: CameraRow
    person_count: int
    recent_violations: int
    score: float
    online: bool


@dataclass(frozen=True)
class Stats:
    total: int
    by_type: dict[str, int]


@dataclass(frozen=True)
class SyncReport:
    cameras: int
    videos: int
    unmatched_folders: list[str]


def node_summary(node: Node, cluster_name: str) -> NodeSummary:
    return NodeSummary(
        id=node.id, name=node.name, cluster_id=node.cluster_id, cluster_name=cluster_name,
        description=node.description, ip_address=node.ip_address,
        max_cameras=node.max_cameras, camera_count=node.camera_count,
    )


def camera_row(camera: Camera, node: Node, cluster_name: str) -> CameraRow:
    return CameraRow(
        id=camera.id, name=camera.name, zone=camera.zone, enabled=camera.enabled,
        node_id=node.id, node_name=node.name, cluster_id=node.cluster_id, cluster_name=cluster_name,
    )


@dataclass(frozen=True)
class OverlayBox:
    label: str
    confidence: float
    box: tuple[int, int, int, int]  # x1, y1, x2, y2 in the pixels of the frame
    track_id: int | None


@dataclass(frozen=True)
class Overlay:
    """The boxes of one frame, for the web to draw over the video."""

    camera_id: int
    position_sec: float  # of that frame in the camera's timeline
    width: int
    height: int
    boxes: tuple[OverlayBox, ...]


@dataclass(frozen=True)
class LiveFrame:
    """A frame of a camera with the boxes found on it, so the web shows both of the same moment."""

    seq: int
    jpeg: bytes
    overlay: Overlay | None
    edge: tuple[float, float, int] | None = None  # the edge speed on this camera: detections/s, ms each, frames dropped
    age_sec: float = 0.0  # how long the frame waited in the cloud before it was sent

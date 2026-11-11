"""What the API returns. The mappers live with the use cases (cloud.application.dto.views) and are shared with MCP;
the models below are the REST contract: routes declare them as response_model."""

from pydantic import BaseModel

from cloud.application.dto.views import (
    camera_out,
    cluster_out,
    detection_out,
    event_out,
    grid_item_out,
    node_out,
    stats_out,
    user_out,
)

__all__ = [
    "ZoneOut",
    "CameraOut",
    "CameraStatusOut",
    "ClusterOut",
    "CompareOut",
    "DetectionOut",
    "EventOut",
    "FrameOut",
    "GridItemOut",
    "LoginOut",
    "NodeOut",
    "RankItemOut",
    "StatsOut",
    "SyncOut",
    "TrendPointOut",
    "TypeCountOut",
    "UserOut",
    "ViolationEventOut",
    "VideoUploadOut",
    "ViolationSummaryOut",
    "camera_out",
    "cluster_out",
    "detection_out",
    "event_out",
    "grid_item_out",
    "node_out",
    "stats_out",
    "user_out",
]


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    cluster_ids: list[int]


class ClusterOut(BaseModel):
    id: int
    name: str
    description: str | None


class NodeOut(BaseModel):
    id: int
    name: str
    cluster_id: int
    cluster_name: str
    description: str | None
    ip_address: str | None
    max_cameras: int
    camera_count: int


class CameraOut(BaseModel):
    id: int
    name: str
    zone: str | None
    enabled: bool
    node_id: int
    node_name: str
    cluster_id: int
    cluster_name: str
    videos: list[str]


class EventOut(BaseModel):
    id: int
    camera_id: int
    violation_type: str
    confidence: float
    created_at: str


class DetectedObjectOut(BaseModel):
    label: str
    confidence: float
    box: list[int]


class DetectionOut(BaseModel):
    detections: list[DetectedObjectOut]
    annotated_jpeg_b64: str


class LoginOut(BaseModel):
    access_token: str
    user: UserOut


class GridItemOut(BaseModel):
    camera_id: int
    name: str
    zone: str | None
    node_id: int
    node_name: str
    cluster_id: int
    cluster_name: str
    person_count: int
    violation_count_recent: int
    score: float
    online: bool
    stream_url: str


class StatsOut(BaseModel):
    total: int
    by_type: dict[str, int]


class CameraStatusOut(BaseModel):
    id: int
    name: str
    enabled: bool
    cluster: str
    node: str
    people_now: int
    violations_last_10_min: int
    videos: list[str]


class VideoUploadOut(BaseModel):
    camera_id: int
    video: str
    videos: list[str]


class SyncOut(BaseModel):
    cameras: int
    videos: int
    unmatched_folders: list[str]


class ViolationEventOut(BaseModel):
    event_id: int
    camera: str
    violation_type: str
    confidence: float
    at: str


class ViolationSummaryOut(BaseModel):
    since_minutes: int
    total: int
    by_type: dict[str, int]
    by_camera: dict[str, int]
    events: list[ViolationEventOut]


class FrameOut(BaseModel):
    event_id: int
    violation_type: str
    at: str


class TrendPointOut(BaseModel):
    bucket: str
    violations: int


class RankItemOut(BaseModel):
    """The key naming the ranked thing is the `by` query value (camera, node, cluster or type)."""

    model_config = {"extra": "allow"}

    violations: int


class TypeCountOut(BaseModel):
    current: int
    previous: int


class CompareOut(BaseModel):
    window_minutes: int
    current_total: int
    previous_total: int
    by_type: dict[str, TypeCountOut]


class ZoneOut(BaseModel):
    id: int
    name: str
    polygon: list[tuple[float, float]]
    enabled: bool

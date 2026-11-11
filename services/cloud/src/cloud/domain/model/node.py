"""A node and the cameras attached to it. Node is the aggregate root: cameras are only changed through it,
so the capacity rule cannot be skipped."""

from dataclasses import dataclass, field

from shared.errors import Conflict, Invalid, NotAllowed
from shared.text import required_name

_CAMERA_FIELDS = {"name", "zone", "enabled"}


@dataclass
class Camera:
    """A video source. Identity is its id; its videos live in a folder named by cluster, node and camera id."""

    name: str
    zone: str | None = None
    enabled: bool = True
    id: int | None = None

    def update(self, **changes) -> None:
        unknown = set(changes) - _CAMERA_FIELDS
        if unknown:
            raise Invalid(f"Không sửa được: {sorted(unknown)}")
        if "name" in changes:
            self.name = required_name(changes["name"], "camera")
        if "zone" in changes:
            self.zone = changes["zone"]
        if "enabled" in changes:
            self.enabled = bool(changes["enabled"])


@dataclass
class Node:
    """An edge machine inside a cluster. It runs the model for all its cameras."""

    cluster_id: int
    name: str
    max_cameras: int = 16
    description: str | None = None
    ip_address: str | None = None
    cameras: list[Camera] = field(default_factory=list)
    id: int | None = None

    def __post_init__(self) -> None:
        self.name = required_name(self.name, "node")
        if self.max_cameras < 1:
            raise Invalid("Node phải chứa được ít nhất 1 camera")

    @property
    def camera_count(self) -> int:
        return len(self.cameras)

    def add_camera(self, name: str, zone: str | None = None, enabled: bool = True) -> Camera:
        if self.camera_count >= self.max_cameras:
            raise Conflict(f"Node đã đủ {self.max_cameras} camera")
        camera = Camera(name=required_name(name, "camera"), zone=zone, enabled=enabled)
        self.cameras.append(camera)
        return camera

    def camera(self, camera_id: int) -> Camera:
        for camera in self.cameras:
            if camera.id == camera_id:
                return camera
        raise NotAllowed(f"Không tìm thấy camera {camera_id}")

    def remove_camera(self, camera_id: int) -> Camera:
        camera = self.camera(camera_id)
        self.cameras.remove(camera)
        return camera

    def reconfigure(
        self, *, name: str, cluster_id: int, max_cameras: int, description: str | None, ip_address: str | None
    ) -> None:
        if cluster_id != self.cluster_id and self.cameras:
            raise Conflict("Node còn camera, không thể chuyển sang cluster khác")
        if max_cameras < self.camera_count:
            raise Conflict("Giới hạn nhỏ hơn số camera đang có")
        self.name = required_name(name, "node")
        self.cluster_id = cluster_id
        self.max_cameras = max_cameras
        self.description = description
        self.ip_address = ip_address

"""Cameras: add, change, remove, and the video files they play. A camera is always changed through its node."""

from typing import BinaryIO

from cloud.application.ports import FeedControl, VideoStore
from cloud.application.dto.read_models import CameraDetail, SyncReport, camera_row
from cloud.application.unit_of_work import UnitOfWorkFactory
from cloud.domain.model.node import Camera, Node
from shared.errors import Invalid, NotAllowed
from shared.text import found
from shared.viewer import Viewer

_VIDEO_TYPES_MESSAGE = "Chỉ nhận file .mp4, .avi, .mkv"


class CameraService:
    def __init__(self, uow: UnitOfWorkFactory, feeds: FeedControl, videos: VideoStore) -> None:
        self._uow, self._feeds, self._videos = uow, feeds, videos

    def create(self, node_id: int, name: str, zone: str | None = None, enabled: bool = True) -> CameraDetail:
        with self._uow() as uow:
            node = found(uow.nodes.get(node_id), "Không tìm thấy node")
            camera = node.add_camera(name, zone, enabled)
            uow.nodes.save(node)
            cluster_name = found(uow.clusters.get(node.cluster_id), "Không tìm thấy cluster").name
        self._open(node, camera)
        return CameraDetail(camera_row(camera, node, cluster_name), [])

    def create_with_video(
        self, viewer: Viewer, node_id: int, name: str, filename: str, content: BinaryIO
    ) -> CameraDetail:
        """A camera and its first video in one step. The viewer needs access to the node's cluster."""
        self._require_video_name(filename)
        with self._uow() as uow:
            node = uow.nodes.get(node_id)
            if node is None or not viewer.can_access_cluster(node.cluster_id):
                raise NotAllowed("Không tìm thấy node")
            camera = node.add_camera(name)
            uow.nodes.save(node)
            cluster_name = found(uow.clusters.get(node.cluster_id), "Không tìm thấy cluster").name
        self._videos.ensure_folder(node.cluster_id, node.id, camera.id)
        self._videos.save(node.cluster_id, node.id, camera.id, filename, content)
        self._open(node, camera)
        return CameraDetail(camera_row(camera, node, cluster_name), self._videos_of(node, camera))

    def update(self, camera_id: int, **changes) -> CameraDetail:
        """`changes` holds any of name, zone, enabled."""
        with self._uow() as uow:
            node = found(uow.nodes.get_by_camera(camera_id), "Không tìm thấy camera")
            camera = node.camera(camera_id)
            camera.update(**changes)
            uow.nodes.save(node)
            cluster_name = found(uow.clusters.get(node.cluster_id), "Không tìm thấy cluster").name
        return CameraDetail(camera_row(camera, node, cluster_name), self._videos_of(node, camera))

    def delete(self, camera_id: int) -> None:
        """Removes the camera. Its video files stay on disk."""
        with self._uow() as uow:
            node = found(uow.nodes.get_by_camera(camera_id), "Không tìm thấy camera")
            node.remove_camera(camera_id)
            uow.nodes.save(node)
        self._feeds.drop(camera_id)

    def add_video(self, viewer: Viewer, camera_id: int, filename: str, content: BinaryIO) -> list[str]:
        """Stores a video in the camera's folder and returns the camera's videos. Cameras play them in name order."""
        self._require_video_name(filename)
        with self._uow() as uow:
            node = uow.nodes.get_by_camera(camera_id)
            if node is None or not viewer.can_access_cluster(node.cluster_id):
                raise NotAllowed("Không tìm thấy camera")
        self._videos.ensure_folder(node.cluster_id, node.id, camera_id)
        self._videos.save(node.cluster_id, node.id, camera_id, filename, content)
        return self._videos.list_videos(node.cluster_id, node.id, camera_id)

    def sync_folders(self) -> SyncReport:
        """Creates the folder of every camera that lacks one, and reports folders no camera owns.
        Unknown folders are reported, never turned into cameras."""
        with self._uow() as uow:
            rows = uow.cameras.rows()
        known = {(r.cluster_id, r.node_id, r.id) for r in rows}
        for cluster_id, node_id, camera_id in known:
            self._videos.ensure_folder(cluster_id, node_id, camera_id)
        unmatched = sorted(f"{c}/{n}/{cam}" for c, n, cam in self._videos.folders_on_disk() - known)
        videos = sum(len(self._videos.list_videos(c, n, cam)) for c, n, cam in known)
        return SyncReport(cameras=len(known), videos=videos, unmatched_folders=unmatched)

    def resume_feeds(self) -> None:
        """Starts a feed for every enabled camera. Called once at startup."""
        with self._uow() as uow:
            rows = uow.cameras.rows()
        for r in rows:
            if r.enabled:
                self._feeds.ensure(r.id, self._videos.folder(r.cluster_id, r.node_id, r.id))

    def _open(self, node: Node, camera: Camera) -> None:
        folder = self._videos.ensure_folder(node.cluster_id, node.id, camera.id)
        if camera.enabled:
            self._feeds.ensure(camera.id, folder)

    def _videos_of(self, node: Node, camera: Camera) -> list[str]:
        return self._videos.list_videos(node.cluster_id, node.id, camera.id)

    def _require_video_name(self, filename: str) -> None:
        if not self._videos.is_video_name(filename):
            raise Invalid(_VIDEO_TYPES_MESSAGE)

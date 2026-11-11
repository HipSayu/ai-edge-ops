"""What exists: clusters, nodes, cameras, users. Read only, scoped to the viewer."""

from datetime import UTC, datetime, timedelta

from cloud.application.ports import FeedControl, VideoStore
from cloud.application.dto.read_models import (
    CameraDetail,
    CameraRow,
    CameraStatus,
    ClusterSummary,
    NodeSummary,
    UserSummary,
    node_summary,
)
from cloud.application.dto.scope import visible_cameras
from cloud.application.unit_of_work import UnitOfWorkFactory
from cloud.domain.model.cluster import Cluster
from shared.errors import Forbidden
from shared.roles import Role
from shared.viewer import Viewer

_RECENT = timedelta(minutes=10)


class CatalogService:
    def __init__(self, uow: UnitOfWorkFactory, feeds: FeedControl, videos: VideoStore) -> None:
        self._uow, self._feeds, self._videos = uow, feeds, videos

    def clusters(self, viewer: Viewer) -> list[Cluster]:
        with self._uow() as uow:
            return [c for c in uow.clusters.list() if viewer.can_access_cluster(c.id)]

    def cluster_summaries(self, viewer: Viewer) -> list[ClusterSummary]:
        with self._uow() as uow:
            node_counts: dict[int, int] = {}
            for node in uow.nodes.list():
                node_counts[node.cluster_id] = node_counts.get(node.cluster_id, 0) + 1
            return [
                ClusterSummary(c.id, c.name, c.description, node_counts.get(c.id, 0))
                for c in uow.clusters.list()
                if viewer.can_access_cluster(c.id)
            ]

    def nodes(self, viewer: Viewer, cluster_id: int | None = None) -> list[NodeSummary]:
        with self._uow() as uow:
            names = {c.id: c.name for c in uow.clusters.list()}
            return [
                node_summary(n, names[n.cluster_id])
                for n in uow.nodes.list(cluster_id)
                if viewer.can_access_cluster(n.cluster_id)
            ]

    def cameras(self, viewer: Viewer, cluster_id: int | None = None, node_id: int | None = None) -> list[CameraRow]:
        with self._uow() as uow:
            rows = visible_cameras(uow, viewer, cluster_id=cluster_id)
        return [r for r in rows.values() if node_id is None or r.node_id == node_id]

    def camera_details(self, viewer: Viewer) -> list[CameraDetail]:
        return [
            CameraDetail(r, self._videos.list_videos(r.cluster_id, r.node_id, r.id)) for r in self.cameras(viewer)
        ]

    def camera_status(self, viewer: Viewer, camera_id: int) -> CameraStatus:
        since = datetime.now(UTC) - _RECENT
        with self._uow() as uow:
            r = visible_cameras(uow, viewer, camera_id=camera_id)[camera_id]
            recent = uow.events.counts_by_camera({camera_id}, since).get(camera_id, 0)
        return CameraStatus(
            id=r.id, name=r.name, enabled=r.enabled, cluster=r.cluster_name, node=r.node_name,
            people_now=self._feeds.person_count(camera_id), violations_last_10_min=recent,
            videos=self._videos.list_videos(r.cluster_id, r.node_id, r.id),
        )

    def users(self, viewer: Viewer) -> list[UserSummary]:
        if viewer.role is not Role.ADMIN:
            raise Forbidden("Chỉ ADMIN được xem danh sách người dùng")
        with self._uow() as uow:
            names = {c.id: c.name for c in uow.clusters.list()}
            return [
                UserSummary(
                    id=u.id, username=u.username, full_name=u.full_name, role=u.role.value,
                    active=u.is_active, clusters=[names[i] for i in u.cluster_ids if i in names],
                )
                for u in uow.users.list()
            ]



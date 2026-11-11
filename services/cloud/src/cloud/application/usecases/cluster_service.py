"""Clusters (construction sites): create, rename, delete."""

from cloud.application.ports import FeedControl
from cloud.application.unit_of_work import UnitOfWorkFactory
from cloud.domain.model.cluster import Cluster
from shared.errors import Conflict
from shared.text import found


class ClusterService:
    def __init__(self, uow: UnitOfWorkFactory, feeds: FeedControl) -> None:
        self._uow, self._feeds = uow, feeds

    def create(self, name: str, description: str | None = None) -> Cluster:
        with self._uow() as uow:
            cluster = Cluster(name=name, description=description)
            self._ensure_unique(uow, cluster)
            return uow.clusters.add(cluster)

    def update(self, cluster_id: int, name: str, description: str | None) -> Cluster:
        with self._uow() as uow:
            cluster = found(uow.clusters.get(cluster_id), "Không tìm thấy cluster")
            cluster.rename(name, description)
            self._ensure_unique(uow, cluster)
            uow.clusters.save(cluster)
            return cluster

    def delete(self, cluster_id: int) -> None:
        """Deletes the nodes and cameras inside too. Video files on disk are kept."""
        with self._uow() as uow:
            found(uow.clusters.get(cluster_id), "Không tìm thấy cluster")
            camera_ids = [c.id for node in uow.nodes.list(cluster_id) for c in node.cameras]
            uow.clusters.remove(cluster_id)
        for camera_id in camera_ids:
            self._feeds.drop(camera_id)

    @staticmethod
    def _ensure_unique(uow, cluster: Cluster) -> None:
        other = uow.clusters.by_name(cluster.name)
        if other is not None and other.id != cluster.id:
            raise Conflict(f"Đã có cluster tên '{cluster.name}'")

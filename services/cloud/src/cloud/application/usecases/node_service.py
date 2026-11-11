"""Nodes (edge machines): create, change, delete. Their cameras go with them."""

from cloud.application.ports import FeedControl
from cloud.application.dto.read_models import NodeSummary, node_summary
from cloud.application.unit_of_work import UnitOfWorkFactory
from cloud.domain.model.node import Node
from shared.text import found


class NodeService:
    def __init__(self, uow: UnitOfWorkFactory, feeds: FeedControl) -> None:
        self._uow, self._feeds = uow, feeds

    def create(
        self, *, cluster_id: int, name: str, max_cameras: int = 16,
        description: str | None = None, ip_address: str | None = None,
    ) -> NodeSummary:
        with self._uow() as uow:
            cluster = found(uow.clusters.get(cluster_id), "Không tìm thấy cluster")
            node = uow.nodes.add(
                Node(cluster_id=cluster_id, name=name, max_cameras=max_cameras,
                     description=description, ip_address=ip_address)
            )
            return node_summary(node, cluster.name)

    def update(
        self, node_id: int, *, cluster_id: int, name: str, max_cameras: int,
        description: str | None, ip_address: str | None,
    ) -> NodeSummary:
        with self._uow() as uow:
            node = found(uow.nodes.get(node_id), "Không tìm thấy node")
            cluster = found(uow.clusters.get(cluster_id), "Không tìm thấy cluster")
            node.reconfigure(
                name=name, cluster_id=cluster_id, max_cameras=max_cameras,
                description=description, ip_address=ip_address,
            )
            uow.nodes.save(node)
            return node_summary(node, cluster.name)

    def delete(self, node_id: int) -> None:
        with self._uow() as uow:
            node = found(uow.nodes.get(node_id), "Không tìm thấy node")
            camera_ids = [c.id for c in node.cameras]
            uow.nodes.remove(node_id)
        for camera_id in camera_ids:
            self._feeds.drop(camera_id)

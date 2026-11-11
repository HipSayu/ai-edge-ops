"""The forbidden zones of a camera: who may see and change them, and telling the edge when they change."""

import logging

from cloud.application.ports import ZonePublisher
from cloud.application.unit_of_work import UnitOfWorkFactory
from cloud.domain.model.zone import MAX_ZONES_PER_CAMERA, Zone
from shared.errors import Invalid, NotAllowed
from shared.viewer import Viewer

log = logging.getLogger("ppe.zones")


class ZoneService:
    def __init__(self, uow: UnitOfWorkFactory, publisher: ZonePublisher | None = None) -> None:
        self._uow, self._publisher = uow, publisher

    def for_camera(self, viewer: Viewer, camera_id: int) -> list[Zone]:
        with self._uow() as uow:
            self._require_access(uow, viewer, camera_id)
            return uow.zones.for_camera(camera_id)

    def replace(self, viewer: Viewer, camera_id: int, zones: list[Zone]) -> list[Zone]:
        """Makes `zones` the camera's zones, then sends them to the edge. The drawing on the web is the whole list, so an
        omitted zone is a deleted one. The edge is told after the change is saved: a camera never has zones the cloud lacks."""
        if len(zones) > MAX_ZONES_PER_CAMERA:
            raise Invalid(f"Một camera có tối đa {MAX_ZONES_PER_CAMERA} vùng cấm")
        with self._uow() as uow:
            self._require_access(uow, viewer, camera_id)
            saved = uow.zones.replace(camera_id, zones)
        self._tell_the_edge(camera_id, saved)
        return saved

    def publish_all(self) -> int:
        """Sends the zones of every camera that has some, so the broker's retained copies match the database (it may have been
        reset, or a node may have been added before the zones were). Returns how many cameras were sent."""
        if self._publisher is None:
            return 0
        with self._uow() as uow:
            sent = 0
            for row in uow.cameras.rows():
                zones = uow.zones.for_camera(row.id)
                if zones:
                    self._tell_the_edge(row.id, zones)
                    sent += 1
        return sent

    @staticmethod
    def _require_access(uow, viewer: Viewer, camera_id: int) -> None:
        node = uow.nodes.get_by_camera(camera_id)
        if node is None or not viewer.can_access_cluster(node.cluster_id):
            raise NotAllowed("Không tìm thấy camera")

    def _tell_the_edge(self, camera_id: int, zones: list[Zone]) -> None:
        if self._publisher is None:
            return
        try:
            if not self._publisher.publish(camera_id, zones):
                log.warning("the zones of camera %s could not be sent to the edge", camera_id)
        except Exception:  # the change is saved; the next start sends it again
            log.exception("the zones of camera %s could not be sent to the edge", camera_id)

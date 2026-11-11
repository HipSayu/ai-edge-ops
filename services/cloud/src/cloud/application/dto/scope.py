from cloud.application.dto.read_models import CameraRow
from cloud.application.unit_of_work import UnitOfWork
from cloud.domain.policy.access_policy import allowed_camera_ids
from shared.text import found
from shared.viewer import Viewer


def visible_cameras(
    uow: UnitOfWork, viewer: Viewer, *, cluster_id: int | None = None, camera_id: int | None = None
) -> dict[int, CameraRow]:
    """The cameras the viewer may use, narrowed by optional filters. One rule for every read."""
    all_rows = uow.cameras.rows()
    allowed = allowed_camera_ids(viewer.role, set(viewer.cluster_ids), [(r.id, r.cluster_id) for r in all_rows])
    rows = {r.id: r for r in all_rows if r.id in allowed}
    if camera_id is not None:
        rows = {camera_id: found(rows.get(camera_id), f"Không tìm thấy camera {camera_id} trong phạm vi của bạn")}
    if cluster_id is not None:
        rows = {cid: r for cid, r in rows.items() if r.cluster_id == cluster_id}
    return rows

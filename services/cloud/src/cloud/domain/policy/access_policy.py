"""Who may see which camera: one rule, used by every use case."""

from collections.abc import Iterable

from shared.roles import Role


def allowed_camera_ids(role: Role, cluster_ids: set[int], cameras: Iterable[tuple[int, int]]) -> set[int]:
    """`cameras` are (camera_id, cluster_id) pairs, the cluster being the one of the camera's node.
    ADMIN sees all; others see cameras in their clusters only."""
    if role is Role.ADMIN:
        return {camera_id for camera_id, _ in cameras}
    return {camera_id for camera_id, cluster_id in cameras if cluster_id in cluster_ids}

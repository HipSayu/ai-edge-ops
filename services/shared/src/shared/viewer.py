"""The signed-in user as the rules see them: who they are and which clusters they may open.

Built from the token's claims by the services that verify it, and by cloud from its own database."""

from dataclasses import dataclass

from shared.errors import Forbidden
from shared.roles import Role, has_at_least


@dataclass(frozen=True)
class Viewer:
    id: int
    username: str
    full_name: str
    role: Role
    cluster_ids: tuple[int, ...]

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN

    def can_access_cluster(self, cluster_id: int) -> bool:
        return self.is_admin or cluster_id in self.cluster_ids

    def require_cluster(self, cluster_id: int) -> None:
        if not self.can_access_cluster(cluster_id):
            raise Forbidden("Không có quyền xem cluster này")

    def require_role(self, minimum: Role) -> None:
        if not has_at_least(self.role, minimum):
            raise Forbidden("Không đủ quyền thực hiện thao tác này")

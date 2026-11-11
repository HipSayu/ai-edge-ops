from dataclasses import dataclass, field

from shared.roles import Role
from shared.viewer import Viewer


@dataclass
class User:
    """An account. ADMIN sees every cluster, so it keeps no cluster assignments."""

    username: str
    password_hash: str
    full_name: str
    role: Role
    is_active: bool = True
    cluster_ids: list[int] = field(default_factory=list)
    id: int | None = None

    def __post_init__(self) -> None:
        self.cluster_ids = [] if self.role is Role.ADMIN else sorted(set(self.cluster_ids))

    def update_profile(self, *, full_name: str, role: Role, is_active: bool, cluster_ids: list[int]) -> None:
        self.full_name = full_name
        self.role = role
        self.is_active = is_active
        self.cluster_ids = [] if role is Role.ADMIN else sorted(set(cluster_ids))

    def to_viewer(self) -> Viewer:
        return Viewer(
            id=self.id, username=self.username, full_name=self.full_name,
            role=self.role, cluster_ids=tuple(self.cluster_ids),
        )

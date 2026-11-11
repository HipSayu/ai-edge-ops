"""Input for the configuration routes: users, clusters, nodes. ADMIN only."""

from pydantic import BaseModel


class UserIn(BaseModel):
    username: str
    password: str | None = None  # required on create, optional on update
    full_name: str
    role: str  # VIEWER | OPERATOR | ADMIN
    is_active: bool = True
    cluster_ids: list[int] = []


class ClusterIn(BaseModel):
    name: str
    description: str | None = None


class NodeIn(BaseModel):
    name: str
    cluster_id: int
    max_cameras: int = 16
    description: str | None = None
    ip_address: str | None = None

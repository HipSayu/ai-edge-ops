"""Users, clusters and nodes: the configuration of the system. Changes are ADMIN-only."""

from fastapi import APIRouter, Depends

from cloud.interface.rest.deps import current_user, get_container, require_role
from cloud.interface.rest.schemas.admin import ClusterIn, NodeIn, UserIn
from cloud.interface.rest.schemas.responses import ClusterOut, NodeOut, UserOut, cluster_out, node_out, user_out
from cloud.bootstrap.container import Container
from shared.roles import Role
from shared.viewer import Viewer

_ADMIN = Depends(require_role(Role.ADMIN))

users = APIRouter(prefix="/users", tags=["users"])


@users.get("", dependencies=[_ADMIN], response_model=list[UserOut])
def list_users(container: Container = Depends(get_container)):
    return [user_out(u) for u in container.users.all()]


@users.post("", status_code=201, dependencies=[_ADMIN], response_model=UserOut)
def create_user(body: UserIn, container: Container = Depends(get_container)):
    return user_out(container.users.create(**body.model_dump()))


@users.put("/{user_id}", dependencies=[_ADMIN], response_model=UserOut)
def update_user(user_id: int, body: UserIn, container: Container = Depends(get_container)):
    return user_out(container.users.update(user_id, **body.model_dump(exclude={"username"})))


@users.delete("/{user_id}", status_code=204, dependencies=[_ADMIN])
def delete_user(user_id: int, container: Container = Depends(get_container)):
    container.users.delete(user_id)


clusters = APIRouter(prefix="/clusters", tags=["clusters"])


@clusters.get("", response_model=list[ClusterOut])
def list_clusters(viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    return [cluster_out(c) for c in container.catalog.clusters(viewer)]


@clusters.post("", status_code=201, dependencies=[_ADMIN], response_model=ClusterOut)
def create_cluster(body: ClusterIn, container: Container = Depends(get_container)):
    return cluster_out(container.clusters.create(body.name, body.description))


@clusters.put("/{cluster_id}", dependencies=[_ADMIN], response_model=ClusterOut)
def update_cluster(cluster_id: int, body: ClusterIn, container: Container = Depends(get_container)):
    return cluster_out(container.clusters.update(cluster_id, body.name, body.description))


@clusters.delete("/{cluster_id}", status_code=204, dependencies=[_ADMIN])
def delete_cluster(cluster_id: int, container: Container = Depends(get_container)):
    """Deletes the nodes and cameras inside too. Video files on disk are kept."""
    container.clusters.delete(cluster_id)


nodes = APIRouter(prefix="/nodes", tags=["nodes"])


@nodes.get("", response_model=list[NodeOut])
def list_nodes(
    cluster_id: int | None = None,
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    return [node_out(n) for n in container.catalog.nodes(viewer, cluster_id)]


@nodes.post("", status_code=201, dependencies=[_ADMIN], response_model=NodeOut)
def create_node(body: NodeIn, container: Container = Depends(get_container)):
    return node_out(container.nodes.create(**body.model_dump()))


@nodes.put("/{node_id}", dependencies=[_ADMIN], response_model=NodeOut)
def update_node(node_id: int, body: NodeIn, container: Container = Depends(get_container)):
    return node_out(container.nodes.update(node_id, **body.model_dump()))


@nodes.delete("/{node_id}", status_code=204, dependencies=[_ADMIN])
def delete_node(node_id: int, container: Container = Depends(get_container)):
    container.nodes.delete(node_id)

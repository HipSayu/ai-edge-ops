from fastapi import APIRouter, Depends, status

from apps.cloud.api.v1.schemas import NodeCreate, NodeOut, NodeUpdate
from apps.cloud.dependencies import get_fleet
from src.cloud.application.services.fleet_service import FleetService

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("", response_model=list[NodeOut])
async def list_nodes(cluster_id: str | None = None, fleet: FleetService = Depends(get_fleet)):
    return await fleet.list_nodes(cluster_id)


@router.post("", response_model=NodeOut, status_code=status.HTTP_201_CREATED)
async def register_node(body: NodeCreate, fleet: FleetService = Depends(get_fleet)):
    return await fleet.register_node(body.cluster_id, body.name, body.metadata)


@router.get("/{node_id}", response_model=NodeOut)
async def get_node(node_id: str, fleet: FleetService = Depends(get_fleet)):
    return await fleet.get_node(node_id)


@router.patch("/{node_id}", response_model=NodeOut)
async def update_node(node_id: str, body: NodeUpdate, fleet: FleetService = Depends(get_fleet)):
    return await fleet.update_node(node_id, body.model_dump(exclude_unset=True))


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(node_id: str, fleet: FleetService = Depends(get_fleet)):
    """409 while the node is online or still has runtimes."""
    await fleet.delete_node(node_id)

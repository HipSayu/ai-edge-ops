from fastapi import APIRouter, Depends, status

from apps.cloud.api.v1.schemas import ClusterCreate, ClusterOut, ClusterUpdate
from apps.cloud.dependencies import get_fleet
from src.cloud.application.services.fleet_service import FleetService

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("", response_model=list[ClusterOut])
async def list_clusters(fleet: FleetService = Depends(get_fleet)):
    return await fleet.list_clusters()


@router.post("", response_model=ClusterOut, status_code=status.HTTP_201_CREATED)
async def create_cluster(body: ClusterCreate, fleet: FleetService = Depends(get_fleet)):
    return await fleet.create_cluster(body.name, body.description, body.location, body.metadata)


@router.get("/{cluster_id}", response_model=ClusterOut)
async def get_cluster(cluster_id: str, fleet: FleetService = Depends(get_fleet)):
    return await fleet.get_cluster(cluster_id)


@router.patch("/{cluster_id}", response_model=ClusterOut)
async def update_cluster(cluster_id: str, body: ClusterUpdate, fleet: FleetService = Depends(get_fleet)):
    return await fleet.update_cluster(cluster_id, body.model_dump(exclude_unset=True))


@router.delete("/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster(cluster_id: str, fleet: FleetService = Depends(get_fleet)):
    """409 while any of its nodes is online or still has runtimes."""
    await fleet.delete_cluster(cluster_id)

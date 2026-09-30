from fastapi import APIRouter, Depends, status

from apps.cloud.api.v1.schemas import DeploymentOut
from apps.cloud.dependencies import get_deployment_service
from src.cloud.application.dto.deployment_request import DeploymentRequest
from src.cloud.application.dto.deployment_update import DeploymentUpdate
from src.cloud.application.services.deployment_service import DeploymentService

# create/update/remove return 202: the edge applies them asynchronously.
router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.post("", response_model=DeploymentOut, status_code=status.HTTP_202_ACCEPTED)
async def create_deployment(
    body: DeploymentRequest, service: DeploymentService = Depends(get_deployment_service)
):
    return await service.create(body)


@router.get("", response_model=list[DeploymentOut])
async def list_deployments(node_id: str | None = None, service: DeploymentService = Depends(get_deployment_service)):
    return await service.list(node_id)


@router.get("/{deployment_id}", response_model=DeploymentOut)
async def get_deployment(deployment_id: str, service: DeploymentService = Depends(get_deployment_service)):
    return await service.get(deployment_id)


@router.put("/{deployment_id}", response_model=DeploymentOut, status_code=status.HTTP_202_ACCEPTED)
async def update_deployment(
    deployment_id: str, body: DeploymentUpdate, service: DeploymentService = Depends(get_deployment_service)
):
    return await service.update(deployment_id, body)


@router.delete("/{deployment_id}", response_model=DeploymentOut, status_code=status.HTTP_202_ACCEPTED)
async def remove_deployment(deployment_id: str, service: DeploymentService = Depends(get_deployment_service)):
    return await service.remove(deployment_id)

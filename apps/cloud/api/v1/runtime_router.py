from fastapi import APIRouter, Depends, Query, status

from apps.cloud.api.v1.schemas import DeploymentOut, RuntimeLogOut, RuntimeOut
from apps.cloud.dependencies import get_deployment_service, get_fleet, get_monitoring
from src.cloud.application.services.deployment_service import DeploymentService
from src.cloud.application.services.fleet_service import FleetService
from src.cloud.application.services.monitoring_service import MonitoringService
from src.shared.contracts import CommandType

router = APIRouter(prefix="/runtimes", tags=["runtimes"])


@router.get("", response_model=list[RuntimeOut])
async def list_runtimes(node_id: str | None = None, fleet: FleetService = Depends(get_fleet)):
    return await fleet.list_runtimes(node_id)


@router.get("/{runtime_id}", response_model=RuntimeOut)
async def get_runtime(runtime_id: str, fleet: FleetService = Depends(get_fleet)):
    return await fleet.get_runtime(runtime_id)


@router.get("/{runtime_id}/logs", response_model=list[RuntimeLogOut])
async def runtime_logs(
    runtime_id: str,
    limit: int = Query(200, ge=1, le=2000),
    monitoring: MonitoringService = Depends(get_monitoring),
):
    """Recent container log lines (oldest first), shipped by the edge agent every few seconds."""
    return await monitoring.runtime_logs(runtime_id, limit)


@router.post("/{runtime_id}/{action}", response_model=DeploymentOut, status_code=status.HTTP_202_ACCEPTED)
async def control_runtime(
    runtime_id: str, action: CommandType, deployments: DeploymentService = Depends(get_deployment_service)
):
    return await deployments.control_runtime(runtime_id, action)

from fastapi import APIRouter, Depends

from apps.cloud.api.v1.schemas import AgentOut, RuntimeOut
from apps.cloud.dependencies import get_fleet
from src.cloud.application.services.fleet_service import FleetService

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/{node_id}", response_model=AgentOut)
async def get_agent(node_id: str, fleet: FleetService = Depends(get_fleet)):
    node = await fleet.get_node(node_id)
    runtimes = await fleet.list_runtimes(node_id)
    return AgentOut(
        node_id=node.id,
        cluster_id=node.cluster_id,
        status=node.status,
        agent_version=node.agent_version,
        last_heartbeat_at=node.last_heartbeat_at,
        runtimes=[RuntimeOut.model_validate(r) for r in runtimes],
    )

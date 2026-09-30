from fastapi import APIRouter, Depends

from apps.edge.dependencies import get_state_report_service
from src.edge.application.services.reporting import StateReportService
from src.shared.contracts import NodeState

router = APIRouter(tags=["agent"])


@router.get("/status", response_model=NodeState)
async def node_status(service: StateReportService = Depends(get_state_report_service)):
    return service.build()

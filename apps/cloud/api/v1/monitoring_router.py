from typing import Any

from fastapi import APIRouter, Depends, Query

from apps.cloud.dependencies import get_monitoring
from src.cloud.application.services.monitoring_service import MonitoringService

# Latest telemetry, recent history and events per node.
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/fleet/metrics")
async def fleet_metrics(
    points: int = Query(30, ge=2, le=360),
    bucket_sec: int = Query(10, ge=5, le=3600),
    service: MonitoringService = Depends(get_monitoring),
) -> list[dict[str, Any]]:
    """Fleet-wide time series for the overview charts (oldest first)."""
    return await service.fleet_metrics(points, bucket_sec)


@router.get("/nodes/{node_id}/telemetry")
async def latest(node_id: str, service: MonitoringService = Depends(get_monitoring)) -> dict[str, dict[str, Any]]:
    return await service.latest(node_id)


@router.get("/nodes/{node_id}/telemetry/{kind}")
async def history(
    node_id: str,
    kind: str,
    limit: int = Query(100, ge=1, le=1000),
    service: MonitoringService = Depends(get_monitoring),
) -> list[dict[str, Any]]:
    return await service.history(node_id, kind, limit)


@router.get("/nodes/{node_id}/events")
async def events(
    node_id: str, limit: int = Query(100, ge=1, le=1000), service: MonitoringService = Depends(get_monitoring)
) -> list[dict[str, Any]]:
    return await service.events(node_id, limit)

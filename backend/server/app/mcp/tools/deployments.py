"""Deployment tools — which model version is bound to which device."""

from __future__ import annotations

from dqh.svc_core.transports.http import PaginationParams

from app.mcp._session import session_scope
from app.modules.deployment import DeploymentService
from app.modules.deployment.rules import DeploymentStatus


def _row(d) -> dict:
    return {
        "id": d.id,
        "device_id": d.device_id,
        "model_version_id": d.model_version_id,
        "status": str(d.status),
        "note": d.note,
        "activated_at": d.activated_at.isoformat() if d.activated_at else None,
        "ended_at": d.ended_at.isoformat() if d.ended_at else None,
        "created_at": d.created_at.isoformat(),
    }


async def list_deployments(
    device_id: int | None = None, status: str | None = None, limit: int = 50
) -> dict:
    """List deployments, optionally by device or status
    (pending|active|superseded|failed|rolled_back)."""
    st = DeploymentStatus(status) if status else None
    async with session_scope() as session:
        page = await DeploymentService(session).list(
            device_id=device_id, status=st, params=PaginationParams(page=1, page_size=min(limit, 200))
        )
        return {"total": page.total, "deployments": [_row(d) for d in page.items]}


async def get_deployment(deployment_id: int) -> dict:
    """Detail for one deployment by id."""
    async with session_scope() as session:
        return _row(await DeploymentService(session).get(deployment_id))


async def active_deployment_count() -> dict:
    """How many deployments are currently ACTIVE across the fleet."""
    async with session_scope() as session:
        return {"active": await DeploymentService(session).count_active()}


TOOLS = [list_deployments, get_deployment, active_deployment_count]

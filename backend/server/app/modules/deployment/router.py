"""Deployment HTTP endpoints."""

from __future__ import annotations

from dqh.svc_core.transports.http import ApiResponse, Page, ok
from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession, Pagination
from app.core.bearer_auth import require_permission
from app.modules.deployment.domain import DeploymentStatus
from app.modules.deployment.schemas import DeploymentCreate, DeploymentFailIn, DeploymentOut
from app.modules.deployment.service import DeploymentService

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.post("", response_model=ApiResponse[DeploymentOut], status_code=status.HTTP_201_CREATED)
async def create_deployment(data: DeploymentCreate, db: DbSession, _: object = Depends(require_permission("deployments.manage"))) -> ApiResponse[DeploymentOut]:
    return ok(DeploymentOut.model_validate(await DeploymentService(db).create(data)))


@router.get("", response_model=ApiResponse[Page[DeploymentOut]])
async def list_deployments(
    db: DbSession,
    params: Pagination,
    device_id: int | None = None,
    deployment_status: DeploymentStatus | None = None,
    _: object = Depends(require_permission("deployments.manage")),
) -> ApiResponse[Page[DeploymentOut]]:
    page = await DeploymentService(db).list(
        device_id=device_id, status=deployment_status, params=params
    )
    return ok(
        Page.of([DeploymentOut.model_validate(d) for d in page.items], total=page.total, params=params)
    )


@router.get("/{deployment_id}", response_model=ApiResponse[DeploymentOut])
async def get_deployment(deployment_id: int, db: DbSession, _: object = Depends(require_permission("deployments.manage"))) -> ApiResponse[DeploymentOut]:
    return ok(DeploymentOut.model_validate(await DeploymentService(db).get(deployment_id)))


@router.post("/{deployment_id}/activate", response_model=ApiResponse[DeploymentOut])
async def activate_deployment(deployment_id: int, db: DbSession, _: object = Depends(require_permission("deployments.manage"))) -> ApiResponse[DeploymentOut]:
    return ok(DeploymentOut.model_validate(await DeploymentService(db).activate(deployment_id)))


@router.post("/{deployment_id}/fail", response_model=ApiResponse[DeploymentOut])
async def fail_deployment(
    deployment_id: int, data: DeploymentFailIn, db: DbSession, _: object = Depends(require_permission("deployments.manage"))
) -> ApiResponse[DeploymentOut]:
    deployment = await DeploymentService(db).mark_failed(deployment_id, data.reason)
    return ok(DeploymentOut.model_validate(deployment))


@router.post("/{deployment_id}/rollback", response_model=ApiResponse[DeploymentOut])
async def rollback_deployment(deployment_id: int, db: DbSession, _: object = Depends(require_permission("deployments.manage"))) -> ApiResponse[DeploymentOut]:
    return ok(DeploymentOut.model_validate(await DeploymentService(db).rollback(deployment_id)))

"""Deployment HTTP endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import DbSession, Pagination
from app.core.pagination import Page
from app.modules.deployment.domain import DeploymentStatus
from app.modules.deployment.schemas import DeploymentCreate, DeploymentFailIn, DeploymentOut
from app.modules.deployment.service import DeploymentService

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.post("", response_model=DeploymentOut, status_code=status.HTTP_201_CREATED)
async def create_deployment(data: DeploymentCreate, db: DbSession) -> DeploymentOut:
    return DeploymentOut.model_validate(await DeploymentService(db).create(data))


@router.get("", response_model=Page[DeploymentOut])
async def list_deployments(
    db: DbSession,
    params: Pagination,
    device_id: int | None = None,
    deployment_status: DeploymentStatus | None = None,
) -> Page[DeploymentOut]:
    page = await DeploymentService(db).list(
        device_id=device_id, status=deployment_status, params=params
    )
    return Page.build(
        [DeploymentOut.model_validate(d) for d in page.items], page.total, params
    )


@router.get("/{deployment_id}", response_model=DeploymentOut)
async def get_deployment(deployment_id: int, db: DbSession) -> DeploymentOut:
    return DeploymentOut.model_validate(await DeploymentService(db).get(deployment_id))


@router.post("/{deployment_id}/activate", response_model=DeploymentOut)
async def activate_deployment(deployment_id: int, db: DbSession) -> DeploymentOut:
    return DeploymentOut.model_validate(await DeploymentService(db).activate(deployment_id))


@router.post("/{deployment_id}/fail", response_model=DeploymentOut)
async def fail_deployment(
    deployment_id: int, data: DeploymentFailIn, db: DbSession
) -> DeploymentOut:
    deployment = await DeploymentService(db).mark_failed(deployment_id, data.reason)
    return DeploymentOut.model_validate(deployment)


@router.post("/{deployment_id}/rollback", response_model=DeploymentOut)
async def rollback_deployment(deployment_id: int, db: DbSession) -> DeploymentOut:
    return DeploymentOut.model_validate(await DeploymentService(db).rollback(deployment_id))

"""Deployment HTTP endpoints — deploy a model image to a device."""

from __future__ import annotations

from dqh.svc_core.transports.http import ApiResponse, ok
from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession
from app.modules.deployment.schemas import DeploymentView, DeployRequest
from app.modules.deployment.service import DeployService
from app.modules.iam.bearer_auth import require_permission

router = APIRouter(prefix="/deployments", tags=["deployments"])

_manage = Depends(require_permission("deployments.manage"))


@router.get("", response_model=ApiResponse[list[DeploymentView]])
async def list_deployments(db: DbSession, _: object = _manage) -> ApiResponse[list[DeploymentView]]:
    return ok(await DeployService(db).list())


@router.post("", response_model=ApiResponse[DeploymentView], status_code=status.HTTP_201_CREATED)
async def create_deployment(
    data: DeployRequest, db: DbSession, _: object = _manage
) -> ApiResponse[DeploymentView]:
    return ok(await DeployService(db).deploy(data))

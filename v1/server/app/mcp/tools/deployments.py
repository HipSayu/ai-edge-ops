"""Deployment tools — which model image each device wants vs. is running."""

from __future__ import annotations

from app.core.database import session_scope
from app.modules.deployment import DeployService


async def list_deployments(device_id: str | None = None) -> dict:
    """Per-device deploy state: desired_image, active_image, runtime_status,
    in_sync. Only devices with a desired model image."""
    async with session_scope() as session:
        views = await DeployService(session).list()
    if device_id:
        views = [v for v in views if v.device_id == device_id]
    return {"total": len(views), "deployments": [v.model_dump(mode="json") for v in views]}


async def active_deployment_count() -> dict:
    """How many devices are running the model image they were told to (in_sync)."""
    async with session_scope() as session:
        return {"in_sync": await DeployService(session).count_active()}


TOOLS = [list_deployments, active_deployment_count]

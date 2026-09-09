"""Deployment use-cases.

The model image is resolved against the live registry catalog
(:data:`app.core.model_catalog.model_catalog`); the deploy row only stores the
digest-pinned ref it sent.
"""

from __future__ import annotations

import httpx
from dqh.svc_core.contracts.errors import BadRequestError as BusinessRuleError
from dqh.svc_core.contracts.errors import NotFoundError
from dqh.svc_core.helpers.time import utcnow
from dqh.svc_core.transports.http import Page
from dqh.svc_core.transports.http import PaginationParams as PageParams
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import event_bus
from app.core.model_catalog import model_catalog
from app.modules.agent import AgentService
from app.modules.deployment.event import DeploymentActivated, DeploymentFailed
from app.modules.deployment.models import Deployment
from app.modules.deployment.repository import DeploymentRepository
from app.modules.deployment.rules import DeploymentStatus, can_transition
from app.modules.deployment.schemas import DeploymentCreate


class DeploymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DeploymentRepository(session)
        self.agent = AgentService(session)

    async def get(self, deployment_id: int) -> Deployment:
        deployment = await self.repo.get(deployment_id)
        if deployment is None:
            raise NotFoundError(f"deployment {deployment_id} not found")
        return deployment

    async def list(
        self,
        *,
        device_id: int | None,
        status: DeploymentStatus | None,
        params: PageParams,
    ) -> Page[Deployment]:
        items, total = await self.repo.list_page(
            device_id=device_id, status=status, params=params
        )
        return Page.of(items, total=total, params=params)

    async def create(self, data: DeploymentCreate) -> Deployment:
        await self.agent.get_device(data.device_id)  # 404 if missing
        tag = data.image.rsplit(":", 1)[-1] if "@" not in data.image else data.image
        try:
            image = await model_catalog.get_model(tag)
        except httpx.HTTPStatusError as exc:
            raise NotFoundError(f"model image {data.image!r} not in the registry") from exc

        deployment = Deployment(
            device_id=data.device_id,
            image=image.pinned_ref,
            config=data.config,
            note=data.note,
        )
        await self.repo.add(deployment)
        await self.session.commit()

        if data.activate_now:
            return await self.activate(deployment.id)
        return deployment

    async def activate(self, deployment_id: int) -> Deployment:
        deployment = await self.get(deployment_id)
        self._guard(deployment.status, DeploymentStatus.ACTIVE)

        current = await self.repo.active_for_device(deployment.device_id)
        if current is not None and current.id != deployment.id:
            current.status = DeploymentStatus.SUPERSEDED
            current.ended_at = utcnow()

        deployment.status = DeploymentStatus.ACTIVE
        deployment.activated_at = utcnow()
        await self.session.commit()

        await event_bus.publish(
            DeploymentActivated(
                deployment_id=deployment.id,
                device_id=deployment.device_id,
                image=deployment.image,
                config=dict(deployment.config),
            )
        )
        return deployment

    async def mark_failed(self, deployment_id: int, reason: str) -> Deployment:
        deployment = await self.get(deployment_id)
        self._guard(deployment.status, DeploymentStatus.FAILED)
        deployment.status = DeploymentStatus.FAILED
        deployment.ended_at = utcnow()
        await self.session.commit()
        await event_bus.publish(
            DeploymentFailed(
                deployment_id=deployment.id, device_id=deployment.device_id, reason=reason
            )
        )
        return deployment

    async def rollback(self, deployment_id: int) -> Deployment:
        deployment = await self.get(deployment_id)
        self._guard(deployment.status, DeploymentStatus.ROLLED_BACK)
        deployment.status = DeploymentStatus.ROLLED_BACK
        deployment.ended_at = utcnow()
        await self.session.commit()
        return deployment

    async def count_active(self) -> int:
        return await self.repo.count_active()

    @staticmethod
    def _guard(current: DeploymentStatus, target: DeploymentStatus) -> None:
        if not can_transition(current, target):
            raise BusinessRuleError(f"cannot move deployment from {current} to {target}")

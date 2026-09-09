"""Deployment data access."""

from __future__ import annotations

from dqh.svc_core.persistence.sqlalchemy import BaseRepository
from dqh.svc_core.transports.http import PaginationParams as PageParams
from sqlalchemy import select

from app.modules.deployment.models import Deployment
from app.modules.deployment.rules import DeploymentStatus


class DeploymentRepository(BaseRepository[Deployment]):
    model = Deployment

    async def list_page(
        self,
        *,
        device_id: int | None,
        status: DeploymentStatus | None,
        params: PageParams,
    ) -> tuple[list[Deployment], int]:
        clauses = []
        if device_id is not None:
            clauses.append(Deployment.device_id == device_id)
        if status is not None:
            clauses.append(Deployment.status == status)
        return await self.page(*clauses, order_by=Deployment.created_at.desc(), params=params)

    async def active_for_device(self, device_id: int) -> Deployment | None:
        stmt = select(Deployment).where(
            Deployment.device_id == device_id,
            Deployment.status == DeploymentStatus.ACTIVE,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def count_active(self) -> int:
        return await self.count(Deployment.status == DeploymentStatus.ACTIVE)

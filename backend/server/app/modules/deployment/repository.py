"""Deployment data access."""

from __future__ import annotations

from dqh.svc_core.transports.http import PaginationParams as PageParams
from sqlalchemy import select

from app.modules.deployment.domain import DeploymentStatus
from app.modules.deployment.models import Deployment
from app.shared.repository import BaseRepository


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
        items = await self.list(*clauses, order_by=Deployment.created_at.desc(), params=params)
        total = await self.count(*clauses)
        return items, total

    async def active_for_device(self, device_id: int) -> Deployment | None:
        stmt = select(Deployment).where(
            Deployment.device_id == device_id,
            Deployment.status == DeploymentStatus.ACTIVE,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def count_active(self) -> int:
        return await self.count(Deployment.status == DeploymentStatus.ACTIVE)

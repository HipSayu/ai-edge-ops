"""Agent data access - Device is the desired-config table."""

from __future__ import annotations

from dqh.svc_core.persistence.sqlalchemy import BaseRepository
from sqlalchemy import select

from app.modules.agent.models import Device


class DeviceRepository(BaseRepository[Device]):
    model = Device

    async def get_by_name(self, name: str) -> Device | None:
        return (
            await self.session.execute(select(Device).where(Device.name == name))
        ).scalar_one_or_none()

    async def list_all(self, *, site: str | None) -> list[Device]:
        stmt = select(Device).order_by(Device.name)
        if site:
            stmt = stmt.where(Device.site == site)
        return list((await self.session.execute(stmt)).scalars().all())

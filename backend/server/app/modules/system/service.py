"""System administration use-cases."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.system.models import AppSetting, AuditLog


class SystemService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_settings(self) -> dict[str, AppSetting]:
        rows = (await self.session.scalars(select(AppSetting).order_by(AppSetting.key))).all()
        return {row.key: row for row in rows}

    async def get_setting(self, key: str) -> object | None:
        """The unwrapped value for one key (settings are stored as {"value": ...})."""
        row = await self.session.get(AppSetting, key)
        return row.value.get("value") if row else None

    async def update_settings(self, payload: dict[str, object]) -> dict[str, AppSetting]:
        for key, value in payload.items():
            setting = await self.session.get(AppSetting, key)
            if setting is None:
                setting = AppSetting(key=key, value={"value": value})
                self.session.add(setting)
            else:
                setting.value = {"value": value}
        await self.session.commit()
        return await self.get_settings()

    async def list_audit_logs(self) -> list[AuditLog]:
        return list((await self.session.scalars(select(AuditLog).order_by(AuditLog.id.desc()))).all())

    async def create_audit_log(self, action: str, actor: str, detail: str | None) -> AuditLog:
        row = AuditLog(
            action=action,
            actor=actor,
            detail=detail,
            created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

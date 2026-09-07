"""System administration HTTP adapter."""

from __future__ import annotations

from dqh.svc_core.transports.http import ApiResponse, ok
from fastapi import APIRouter, Body, status

from app.api.deps import DbSession
from app.modules.system.schemas import AuditLogOut, SettingOut
from app.modules.system.service import SystemService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/settings", response_model=ApiResponse[dict[str, SettingOut]])
async def get_settings(db: DbSession) -> ApiResponse[dict[str, SettingOut]]:
    settings = await SystemService(db).get_settings()
    return ok({key: SettingOut.model_validate(value) for key, value in settings.items()})


@router.patch("/settings", response_model=ApiResponse[dict[str, SettingOut]])
async def update_settings(
    db: DbSession, payload: dict[str, object] = Body(...)
) -> ApiResponse[dict[str, SettingOut]]:
    settings = await SystemService(db).update_settings(payload)
    return ok({key: SettingOut.model_validate(value) for key, value in settings.items()})


@router.get("/audit-logs", response_model=ApiResponse[list[AuditLogOut]])
async def list_audit_logs(db: DbSession) -> ApiResponse[list[AuditLogOut]]:
    rows = await SystemService(db).list_audit_logs()
    return ok([AuditLogOut.model_validate(row) for row in rows])


@router.post("/audit-logs", response_model=ApiResponse[AuditLogOut], status_code=status.HTTP_201_CREATED)
async def create_audit_log(
    db: DbSession,
    action: str = Body(...),
    actor: str = Body("system"),
    detail: str | None = Body(None),
) -> ApiResponse[AuditLogOut]:
    row = await SystemService(db).create_audit_log(action, actor, detail)
    return ok(AuditLogOut.model_validate(row))

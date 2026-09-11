"""System tools — app settings and audit log."""

from __future__ import annotations

from app.core.database import session_scope
from app.modules.system.service import SystemService


async def get_settings() -> dict:
    """Current application settings (key -> value)."""
    async with session_scope() as session:
        rows = await SystemService(session).get_settings()
        return {key: row.value for key, row in rows.items()}


async def list_audit_logs(limit: int = 50) -> dict:
    """Recent audit-log entries (who did what)."""
    async with session_scope() as session:
        rows = await SystemService(session).list_audit_logs()
        return {
            "entries": [
                {"action": r.action, "actor": r.actor, "detail": r.detail, "at": r.created_at}
                for r in rows[:limit]
            ]
        }


TOOLS = [get_settings, list_audit_logs]

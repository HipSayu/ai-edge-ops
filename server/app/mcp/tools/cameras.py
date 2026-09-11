"""Camera tools."""

from __future__ import annotations

from app.core.database import session_scope
from app.modules.camera.service import CameraService


async def list_cameras() -> dict:
    """All cameras: id, name, source, zone, and the group they belong to."""
    async with session_scope() as session:
        rows = await CameraService(session).list_cameras()
        return {"cameras": [_safe(c) for c in rows]}


async def list_camera_groups() -> dict:
    """Camera groups."""
    async with session_scope() as session:
        rows = await CameraService(session).list_groups()
        return {"groups": [_safe(g) for g in rows]}


async def list_snapshots(camera_id: int | None = None) -> dict:
    """Recent captured snapshots, optionally for one camera."""
    async with session_scope() as session:
        rows = await CameraService(session).list_snapshots(camera_id=camera_id)
        return {"snapshots": [_safe(s) for s in rows]}


def _safe(obj) -> dict:
    out = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        out[col.name] = val.isoformat() if hasattr(val, "isoformat") else val
    return out


TOOLS = [list_cameras, list_camera_groups, list_snapshots]

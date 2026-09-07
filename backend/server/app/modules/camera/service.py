"""Camera domain use-cases."""

from __future__ import annotations

from dqh.svc_core.contracts.errors import ConflictError, NotFoundError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.camera.models import Camera, CameraGroup, Snapshot
from app.modules.camera.schemas import CameraCreate, CameraGroupCreate, CameraUpdate


class CameraService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_cameras(self) -> list[Camera]:
        return list((await self.session.scalars(select(Camera).order_by(Camera.name))).all())

    async def create_camera(self, data: CameraCreate) -> Camera:
        if await self.session.scalar(select(Camera).where(Camera.name == data.name)):
            raise ConflictError(f"camera '{data.name}' already exists")
        camera = Camera(**data.model_dump())
        self.session.add(camera)
        await self.session.commit()
        await self.session.refresh(camera)
        return camera

    async def get_camera(self, camera_id: int) -> Camera:
        camera = await self.session.get(Camera, camera_id)
        if camera is None:
            raise NotFoundError(f"camera {camera_id} not found")
        return camera

    async def update_camera(self, camera_id: int, data: CameraUpdate) -> Camera:
        camera = await self.get_camera(camera_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(camera, field, value)
        await self.session.commit()
        await self.session.refresh(camera)
        return camera

    async def list_groups(self) -> list[CameraGroup]:
        return list((await self.session.scalars(select(CameraGroup).order_by(CameraGroup.name))).all())

    async def create_group(self, data: CameraGroupCreate) -> CameraGroup:
        if await self.session.scalar(select(CameraGroup).where(CameraGroup.name == data.name)):
            raise ConflictError(f"camera group '{data.name}' already exists")
        group = CameraGroup(**data.model_dump())
        self.session.add(group)
        await self.session.commit()
        await self.session.refresh(group)
        return group

    async def get_group(self, group_id: int) -> CameraGroup:
        group = await self.session.get(CameraGroup, group_id)
        if group is None:
            raise NotFoundError(f"camera group {group_id} not found")
        return group

    async def list_snapshots(self, camera_id: int | None = None) -> list[Snapshot]:
        stmt = select(Snapshot).order_by(Snapshot.id.desc())
        if camera_id is not None:
            stmt = stmt.where(Snapshot.camera_id == camera_id)
        return list((await self.session.scalars(stmt)).all())

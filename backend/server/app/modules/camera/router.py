"""Camera HTTP adapter."""

from __future__ import annotations

from dqh.svc_core.transports.http import ApiResponse, ok
from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.modules.camera.schemas import (
    CameraCreate,
    CameraGroupCreate,
    CameraGroupOut,
    CameraOut,
    CameraUpdate,
    SnapshotOut,
)
from app.modules.camera.service import CameraService

router = APIRouter(prefix="/agent", tags=["cameras"])


@router.get("/cameras", response_model=ApiResponse[list[CameraOut]])
async def list_cameras(db: DbSession) -> ApiResponse[list[CameraOut]]:
    rows = await CameraService(db).list_cameras()
    return ok([CameraOut.model_validate(row) for row in rows])


@router.post("/cameras", response_model=ApiResponse[CameraOut], status_code=status.HTTP_201_CREATED)
async def create_camera(data: CameraCreate, db: DbSession) -> ApiResponse[CameraOut]:
    return ok(CameraOut.model_validate(await CameraService(db).create_camera(data)))


@router.get("/cameras/{camera_id}", response_model=ApiResponse[CameraOut])
async def get_camera(camera_id: int, db: DbSession) -> ApiResponse[CameraOut]:
    return ok(CameraOut.model_validate(await CameraService(db).get_camera(camera_id)))


@router.patch("/cameras/{camera_id}", response_model=ApiResponse[CameraOut])
async def update_camera(camera_id: int, data: CameraUpdate, db: DbSession) -> ApiResponse[CameraOut]:
    return ok(CameraOut.model_validate(await CameraService(db).update_camera(camera_id, data)))


@router.get("/camera-groups", response_model=ApiResponse[list[CameraGroupOut]])
async def list_camera_groups(db: DbSession) -> ApiResponse[list[CameraGroupOut]]:
    rows = await CameraService(db).list_groups()
    return ok([CameraGroupOut.model_validate(row) for row in rows])


@router.post(
    "/camera-groups",
    response_model=ApiResponse[CameraGroupOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_camera_group(data: CameraGroupCreate, db: DbSession) -> ApiResponse[CameraGroupOut]:
    return ok(CameraGroupOut.model_validate(await CameraService(db).create_group(data)))


@router.get("/camera-groups/{group_id}", response_model=ApiResponse[CameraGroupOut])
async def get_camera_group(group_id: int, db: DbSession) -> ApiResponse[CameraGroupOut]:
    return ok(CameraGroupOut.model_validate(await CameraService(db).get_group(group_id)))


@router.get("/snapshots", response_model=ApiResponse[list[SnapshotOut]])
async def list_snapshots(
    db: DbSession, camera_id: int | None = None
) -> ApiResponse[list[SnapshotOut]]:
    rows = await CameraService(db).list_snapshots(camera_id)
    return ok([SnapshotOut.model_validate(row) for row in rows])

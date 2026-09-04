"""Fleet HTTP endpoints."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, status

from app.api.deps import DbSession, Pagination
from app.core.pagination import Page
from app.modules.fleet.domain import DeviceStatus
from app.modules.fleet.schemas import (
    DeviceCreate,
    DeviceOut,
    DeviceUpdate,
    FleetHealth,
    HeartbeatAck,
    HeartbeatIn,
    MetricSampleOut,
)
from app.modules.fleet.service import FleetService

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.post("/devices", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
async def register_device(data: DeviceCreate, db: DbSession) -> DeviceOut:
    device = await FleetService(db).register_device(data)
    return DeviceOut.model_validate(device)


@router.get("/devices", response_model=Page[DeviceOut])
async def list_devices(
    db: DbSession,
    params: Pagination,
    site: str | None = None,
    device_status: DeviceStatus | None = None,
) -> Page[DeviceOut]:
    page = await FleetService(db).list_devices(site=site, status=device_status, params=params)
    return Page.build([DeviceOut.model_validate(d) for d in page.items], page.total, params)


@router.get("/devices/{device_id}", response_model=DeviceOut)
async def get_device(device_id: int, db: DbSession) -> DeviceOut:
    return DeviceOut.model_validate(await FleetService(db).get_device(device_id))


@router.patch("/devices/{device_id}", response_model=DeviceOut)
async def update_device(device_id: int, data: DeviceUpdate, db: DbSession) -> DeviceOut:
    return DeviceOut.model_validate(await FleetService(db).update_device(device_id, data))


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: int, db: DbSession) -> None:
    await FleetService(db).delete_device(device_id)


@router.post("/devices/{device_id}/heartbeat", response_model=HeartbeatAck, status_code=201)
async def record_heartbeat(device_id: int, hb: HeartbeatIn, db: DbSession) -> HeartbeatAck:
    device, sample = await FleetService(db).record_heartbeat(device_id, hb)
    return HeartbeatAck(
        device_id=device.id,
        status=device.status,
        sample=MetricSampleOut.model_validate(sample),
    )


@router.get("/devices/{device_id}/metrics", response_model=Page[MetricSampleOut])
async def list_device_metrics(
    device_id: int,
    db: DbSession,
    params: Pagination,
    since: dt.datetime | None = None,
) -> Page[MetricSampleOut]:
    page = await FleetService(db).list_metrics(device_id, since=since, params=params)
    return Page.build(
        [MetricSampleOut.model_validate(s) for s in page.items], page.total, params
    )


@router.get("/health-summary", response_model=FleetHealth)
async def fleet_health(db: DbSession) -> FleetHealth:
    return await FleetService(db).fleet_health()

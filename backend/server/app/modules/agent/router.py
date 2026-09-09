"""Agent HTTP endpoints."""

from __future__ import annotations

import datetime as dt
import json

from dqh.svc_core.messaging import Envelope
from dqh.svc_core.transports.http import ApiResponse, Page, ok
from dqh.svc_core.transports.websocket.fastapi import serve_ws
from fastapi import APIRouter, WebSocket, status

from app.api.deps import DbSession, Pagination
from app.core.ws import ws_hub
from app.core.ws_auth import authenticate_ws
from app.modules.agent import telemetry_relay
from app.modules.agent.domain import DeviceStatus
from app.modules.agent.schemas import (
    AgentHealth,
    DeviceCreate,
    DeviceOut,
    DeviceUpdate,
    HeartbeatAck,
    HeartbeatIn,
    MetricSampleOut,
)
from app.modules.agent.service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


# --- live updates ------------------------------------------------------------
async def _on_telemetry_message(websocket: WebSocket, raw: str) -> None:
    """Client -> server control frames. ``{"op":"snapshot"}`` replays the
    current per-device values so a freshly opened socket isn't blank until the
    next sample arrives."""
    try:
        op = json.loads(raw).get("op")
    except (ValueError, AttributeError):
        return
    if op == "snapshot":
        for frame in telemetry_relay.snapshot():
            await websocket.send_text(
                Envelope(type="telemetry.device", source="agent", payload=frame).model_dump_json()
            )


@router.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket) -> None:
    """Live metric feed: per-device samples (``telemetry/{device_id}``, ~1s from
    the edge telemetry pump) plus an agent-wide rolling aggregate
    (``telemetry/agent``). Send ``{"op":"snapshot"}`` on connect for current state."""
    await serve_ws(
        websocket,
        ws_hub,
        "telemetry/#",
        authenticate=authenticate_ws,
        on_message=_on_telemetry_message,
    )


@router.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket) -> None:
    """Live log stream from edge agents."""
    await serve_ws(websocket, ws_hub, "logs/#", authenticate=authenticate_ws)


@router.post("/devices", response_model=ApiResponse[DeviceOut], status_code=status.HTTP_201_CREATED)
async def register_device(data: DeviceCreate, db: DbSession) -> ApiResponse[DeviceOut]:
    device = await AgentService(db).register_device(data)
    return ok(DeviceOut.model_validate(device))


@router.get("/devices", response_model=ApiResponse[Page[DeviceOut]])
async def list_devices(
    db: DbSession,
    params: Pagination,
    site: str | None = None,
    device_status: DeviceStatus | None = None,
) -> ApiResponse[Page[DeviceOut]]:
    page = await AgentService(db).list_devices(site=site, status=device_status, params=params)
    return ok(Page.of([DeviceOut.model_validate(d) for d in page.items], total=page.total, params=params))


@router.get("/devices/{device_id}", response_model=ApiResponse[DeviceOut])
async def get_device(device_id: int, db: DbSession) -> ApiResponse[DeviceOut]:
    return ok(DeviceOut.model_validate(await AgentService(db).get_device(device_id)))


@router.patch("/devices/{device_id}", response_model=ApiResponse[DeviceOut])
async def update_device(device_id: int, data: DeviceUpdate, db: DbSession) -> ApiResponse[DeviceOut]:
    return ok(DeviceOut.model_validate(await AgentService(db).update_device(device_id, data)))


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: int, db: DbSession) -> None:
    await AgentService(db).delete_device(device_id)


@router.post(
    "/devices/{device_id}/heartbeat",
    response_model=ApiResponse[HeartbeatAck],
    status_code=status.HTTP_201_CREATED,
)
async def record_heartbeat(
    device_id: int, hb: HeartbeatIn, db: DbSession
) -> ApiResponse[HeartbeatAck]:
    device, sample = await AgentService(db).record_heartbeat(device_id, hb)
    return ok(
        HeartbeatAck(
            device_id=device.id,
            status=device.status,
            sample=MetricSampleOut.model_validate(sample),
        )
    )


@router.get("/devices/{device_id}/metrics", response_model=ApiResponse[Page[MetricSampleOut]])
async def list_device_metrics(
    device_id: int,
    db: DbSession,
    params: Pagination,
    since: dt.datetime | None = None,
) -> ApiResponse[Page[MetricSampleOut]]:
    page = await AgentService(db).list_metrics(device_id, since=since, params=params)
    return ok(
        Page.of(
            [MetricSampleOut.model_validate(s) for s in page.items],
            total=page.total,
            params=params,
        )
    )


@router.get("/health-summary", response_model=ApiResponse[AgentHealth])
async def agent_health(db: DbSession) -> ApiResponse[AgentHealth]:
    return ok(await AgentService(db).agent_health())

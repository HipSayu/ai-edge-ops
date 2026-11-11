"""The live wall, its numbers, camera streams and violation frames."""

import asyncio
import json
import struct
import time
from collections.abc import AsyncIterator, Iterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, StreamingResponse

from cloud.interface.rest.deps import current_user, get_container
from cloud.interface.rest.schemas.responses import GridItemOut, StatsOut, grid_item_out, stats_out
from cloud.bootstrap.container import Container
from shared.errors import Invalid
from shared.viewer import Viewer

router = APIRouter(tags=["monitoring"])
_BOUNDARY = "frame"
_OVERLAY_CAMERAS = 24  # one connection serves a whole wall
_OVERLAY_TICK_SEC = 0.1
_OVERLAY_REFRESH_SEC = 1.0  # a box that did not change is sent again this often, so the page can tell the stream is alive


@router.get("/grid", response_model=list[GridItemOut])
def grid(
    cluster_id: int | None = None,
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    """Cameras the wall shows, already ordered. Cameras with violations or people come first."""
    return [grid_item_out(item) for item in container.monitoring.grid(viewer, cluster_id)]


@router.get("/stats", response_model=StatsOut)
def stats(
    cluster_id: int | None = None,
    since_minutes: int = 60,
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    result = container.monitoring.stats(viewer, cluster_id, since_minutes)
    return stats_out(result)


@router.get("/cameras/{camera_id}/stream")
def stream(camera_id: int, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    """MJPEG of the camera's looping videos with detection boxes. Needs the Authorization header, so the page reads it with fetch."""
    container.monitoring.open_stream(viewer, camera_id)

    def frames() -> Iterator[bytes]:
        last = b""
        while True:
            jpeg = container.monitoring.latest_frame(camera_id)
            if jpeg and jpeg is not last:
                last = jpeg
                yield b"--" + _BOUNDARY.encode() + b"\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            time.sleep(0.04)

    return StreamingResponse(frames(), media_type=f"multipart/x-mixed-replace; boundary={_BOUNDARY}")


def _packet(frame, camera_id: int | None = None) -> bytes:
    """One frame for the web: two lengths (4 bytes each, big endian), a JSON header with the boxes, then the JPEG.
    `camera_id` is only set on the multiplexed wall endpoint, where one connection carries several cameras."""
    overlay = frame.overlay
    speed = frame.edge or (0.0, 0.0, 0)
    header = {"age": round(frame.age_sec * 1000), "edge": {"fps": round(speed[0], 1), "ms": round(speed[1], 1), "drop": speed[2]}, "w": overlay.width if overlay else 0, "h": overlay.height if overlay else 0, "boxes": [
        {"l": b.label, "c": round(b.confidence, 3), "b": list(b.box), "t": b.track_id} for b in overlay.boxes
    ] if overlay else []}
    if camera_id is not None:
        header["id"] = camera_id
    head = json.dumps(header, separators=(",", ":")).encode()
    return struct.pack(">II", len(head), len(frame.jpeg)) + head + frame.jpeg


@router.get("/cameras/{camera_id}/live")
def live(camera_id: int, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    """The camera's frames, each with the boxes found on that very frame (see _packet). The page reads it with fetch,
    so the token can travel in the Authorization header."""
    container.monitoring.open_stream(viewer, camera_id)

    def packets() -> Iterator[bytes]:
        seq = 0
        while True:
            frame = container.monitoring.live_frame(camera_id, seq)
            if frame is None:
                time.sleep(0.01)
                continue
            seq = frame.seq
            yield _packet(frame)

    return StreamingResponse(packets(), media_type="application/octet-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/cameras/live")
async def live_wall(
    request: Request,
    cluster_id: int | None = None,
    pin: int | None = None,
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    """One connection for the whole wall: the frames of exactly the cameras GET /grid would show for this viewer and
    cluster, each packet tagged with its camera (see _packet). The caller never lists cameras itself — the server picks
    the same set /grid just picked, so the two calls always agree without the page tracking ids by hand. `pin` adds one
    more camera even if the grid would not otherwise show it (the one the viewer opened full-screen or from an event).
    Reopen this call whenever cluster_id or pin changes; which cameras are on it can also change between reads of the
    same connection, as the grid itself reorders (violations and people first)."""
    ids = [item.camera.id for item in container.monitoring.grid(viewer, cluster_id)]
    if pin is not None and pin not in ids:
        ids.append(pin)
    if len(ids) > _OVERLAY_CAMERAS:
        ids = ids[:_OVERLAY_CAMERAS]
    container.monitoring.require_streams(viewer, ids)

    async def packets() -> AsyncIterator[bytes]:
        seq = dict.fromkeys(ids, 0)
        while not await request.is_disconnected():
            sent = False
            for camera_id in ids:
                frame = container.monitoring.live_frame(camera_id, seq[camera_id])
                if frame is not None:
                    seq[camera_id] = frame.seq
                    sent = True
                    yield _packet(frame, camera_id)
            if not sent:
                await asyncio.sleep(0.01)

    return StreamingResponse(
        packets(), media_type="application/octet-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _overlay_json(camera_id: int, overlay) -> str:
    body = {"camera_id": camera_id, "w": overlay.width, "h": overlay.height, "boxes": [
        {"l": b.label, "c": round(b.confidence, 3), "b": list(b.box), "t": b.track_id} for b in overlay.boxes
    ]} if overlay else {"camera_id": camera_id, "w": 0, "h": 0, "boxes": []}
    return f"event: overlay\ndata: {json.dumps(body, separators=(',', ':'))}\n\n"


@router.get("/overlay/stream")
async def overlay_stream(
    request: Request,
    camera_ids: str,
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    """Server-sent events with the boxes to draw over the cameras' videos, matched to the frame being shown.
    `camera_ids` is a comma-separated list; one connection serves them all. Needs the Authorization header (fetch, not EventSource)."""
    try:
        ids = sorted({int(part) for part in camera_ids.split(",") if part.strip()})
    except ValueError:
        raise Invalid("camera_ids phải là danh sách số") from None
    if not ids or len(ids) > _OVERLAY_CAMERAS:
        raise Invalid(f"Cần từ 1 đến {_OVERLAY_CAMERAS} camera")
    container.monitoring.require_streams(viewer, ids)

    async def events() -> AsyncIterator[str]:
        last: dict[int, tuple[object, float]] = {}  # camera -> (the boxes sent, when)
        while not await request.is_disconnected():
            now = time.monotonic()
            for camera_id in ids:
                overlay = container.monitoring.overlay(camera_id)
                sent_boxes, sent_at = last.get(camera_id, (False, 0.0))
                if overlay is not sent_boxes or now - sent_at >= _OVERLAY_REFRESH_SEC:
                    last[camera_id] = (overlay, now)
                    yield _overlay_json(camera_id, overlay)
            await asyncio.sleep(_OVERLAY_TICK_SEC)

    return StreamingResponse(
        events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/snapshots/{event_id}")
def snapshot(event_id: int, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    """The frame saved with a violation. Same visibility rule as the camera it came from."""
    return Response(container.monitoring.snapshot(viewer, event_id), media_type="image/jpeg")

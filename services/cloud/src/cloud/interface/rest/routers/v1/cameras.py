"""Cameras and their videos. A camera is always changed through its node on the server."""

from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile

from cloud.interface.rest.deps import current_user, get_container, require_role
from cloud.interface.rest.schemas.cameras import CameraIn, CameraUpdate, ZonesIn
from cloud.interface.rest.schemas.responses import (
    CameraOut,
    CameraStatusOut,
    EventOut,
    SyncOut,
    VideoUploadOut,
    ZoneOut,
    camera_out,
    event_out,
)
from cloud.bootstrap.container import Container
from cloud.domain.model.zone import Zone
from shared.roles import Role
from shared.viewer import Viewer

router = APIRouter(prefix="/cameras", tags=["cameras"])
_ADMIN = Depends(require_role(Role.ADMIN))
_OPERATOR = Depends(require_role(Role.OPERATOR))


def _client_filename(upload: UploadFile) -> str:
    return Path(upload.filename or "").name  # drops any directory part the client sent


@router.get("", response_model=list[CameraOut])
def list_cameras(viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    return [camera_out(d) for d in container.catalog.camera_details(viewer)]


@router.post("", status_code=201, dependencies=[_ADMIN], response_model=CameraOut)
def create_camera(body: CameraIn, container: Container = Depends(get_container)):
    return camera_out(container.cameras.create(body.node_id, body.name, body.zone, body.enabled))


@router.post("/upload", status_code=201, dependencies=[_OPERATOR], response_model=CameraOut)
def upload_new_camera(
    name: str = Form(...),
    node_id: int = Form(...),
    file: UploadFile = File(...),
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    """Creates a camera on a node and stores its first video, in one step (the admin upload form)."""
    detail = container.cameras.create_with_video(viewer, node_id, name, _client_filename(file), file.file)
    return camera_out(detail)


@router.get("/{camera_id}/status", response_model=CameraStatusOut)
def camera_status(camera_id: int, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    return asdict(container.catalog.camera_status(viewer, camera_id))


@router.put("/{camera_id}", dependencies=[_ADMIN], response_model=CameraOut)
def update_camera(camera_id: int, body: CameraUpdate, container: Container = Depends(get_container)):
    return camera_out(container.cameras.update(camera_id, name=body.name, zone=body.zone, enabled=body.enabled))


@router.delete("/{camera_id}", status_code=204, dependencies=[_ADMIN])
def delete_camera(camera_id: int, container: Container = Depends(get_container)):
    """Removes the camera from the database. Its video files stay on disk."""
    container.cameras.delete(camera_id)


@router.post("/{camera_id}/videos", status_code=201, dependencies=[_OPERATOR], response_model=VideoUploadOut)
def upload_video(
    camera_id: int,
    file: UploadFile = File(...),
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    """Stores a video in the camera's folder. The camera plays its videos in name order, looping."""
    filename = _client_filename(file)
    videos = container.cameras.add_video(viewer, camera_id, filename, file.file)
    return {"camera_id": camera_id, "video": filename, "videos": videos}


@router.post("/sync", dependencies=[_OPERATOR], response_model=SyncOut)
def sync_folders(container: Container = Depends(get_container)):
    """Creates the folder of every camera that lacks one, and reports folders no camera owns."""
    return asdict(container.cameras.sync_folders())


@router.get("/{camera_id}/events", response_model=list[EventOut])
def camera_events(
    camera_id: int,
    limit: int = 30,
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    return [event_out(e) for e in container.monitoring.camera_events(viewer, camera_id, limit)]


def _zone_out(zone: Zone) -> dict:
    return {"id": zone.id, "name": zone.name, "polygon": [list(c) for c in zone.polygon], "enabled": zone.enabled}


@router.get("/{camera_id}/zones", response_model=list[ZoneOut])
def list_zones(camera_id: int, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    """The forbidden zones of a camera, drawn on its picture."""
    return [_zone_out(z) for z in container.zones.for_camera(viewer, camera_id)]


@router.put("/{camera_id}/zones", dependencies=[_OPERATOR], response_model=list[ZoneOut])
def replace_zones(
    camera_id: int, body: ZonesIn, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container),
):
    """Makes the list the camera's zones (an omitted zone is deleted) and sends them to the edge that runs the camera."""
    zones = [Zone(name=z.name, polygon=tuple(z.polygon), enabled=z.enabled) for z in body.zones]
    return [_zone_out(z) for z in container.zones.replace(viewer, camera_id, zones)]

"""Test the PPE model on a one-off picture from the dashboard, without a camera. Proxies to the detector app, which
is only reachable on the compose network (no published port)."""

from fastapi import APIRouter, Depends, Request

from cloud.interface.rest.deps import current_user, get_container
from cloud.interface.rest.schemas.responses import DetectionOut, detection_out
from cloud.bootstrap.container import Container
from shared.viewer import Viewer

router = APIRouter(prefix="/detect", tags=["detect"])


@router.post("", response_model=DetectionOut)
async def detect(request: Request, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    image = await request.body()
    return detection_out(container.detect.detect(image))

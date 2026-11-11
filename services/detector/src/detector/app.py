"""The PPE model as a service, over HTTP (see router.py for the routes).

The assistant and cloud call it for pictures they need judged: cloud's dashboard testing a picture, the assistant's
chat attachments. It reuses the edge's detector and renderer, so a picture is judged by the same model, size and
threshold as the cameras are. Only reachable on the compose network: no port is published to the host."""

import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from edge.infrastructure.jpeg_renderer import JpegRenderer
from edge.infrastructure.yolo_detector import YoloDetector

from detector.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.detector = YoloDetector(
        Path(os.environ.get("DETECTOR_MODEL", "/weights/ppe.pt")),
        int(os.environ.get("DETECTOR_IMGSZ", "960")),
        float(os.environ.get("DETECTOR_CONF", "0.35")),
        device=os.environ.get("DETECTOR_DEVICE", "cpu"),
    )
    app.state.renderer = JpegRenderer(quality=88, max_width=1280)
    app.state.lock = threading.Lock()  # one picture at a time: the model is shared
    yield


app = FastAPI(title="PPE detector", lifespan=lifespan)
app.include_router(router)

"""POST /detect with a picture's bytes, answer with what it found and the picture marked."""

import base64

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()
_MAX_BYTES = 12 * 1024 * 1024


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/detect")
async def detect(request: Request) -> dict:
    data = await request.body()
    if not data or len(data) > _MAX_BYTES:
        raise HTTPException(413 if data else 400, "Ảnh trống hoặc quá lớn")
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(400, "Không đọc được ảnh")
    state = request.app.state
    with state.lock:
        detections = state.detector.detect(image)
    marked = state.renderer.render(image, detections)
    return {
        "detections": [{"label": d.label, "confidence": round(d.confidence, 3), "box": list(d.box)} for d in detections],
        "annotated_jpeg_b64": base64.b64encode(marked).decode("ascii"),
    }

"""Ultralytics YOLO runtime. Needs the ``inference`` extra.

    pip install ai-edge-ops-vision-runtime[inference]
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from vision_runtime.runtime.base import Detection, InferenceRuntime

# Fall back to the vendored ultralytics under inference/packages/ultralytics
# when it isn't pip-installed (dev checkouts).
_VENDORED = Path(__file__).resolve().parents[3] / "packages" / "ultralytics"
if _VENDORED.is_dir() and str(_VENDORED) not in sys.path:
    sys.path.insert(0, str(_VENDORED))

try:
    from ultralytics import YOLO
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "YoloRuntime needs the 'inference' extra: pip install ai-edge-ops-vision-runtime[inference]"
    ) from exc


class YoloRuntime(InferenceRuntime):
    def __init__(self, *, device: str = "cpu") -> None:
        self._model: YOLO | None = None
        self._mv_id: int | None = None
        self._device = device
        self._conf = 0.25
        self._iou = 0.5
        self._imgsz = 640

    @property
    def loaded(self) -> bool:
        return self._model is not None

    @property
    def model_version_id(self) -> int | None:
        return self._mv_id

    async def load(self, *, weights_path: str, model_version_id: int, config: dict) -> None:
        self._model = YOLO(weights_path)
        self._mv_id = model_version_id
        self._conf = float(config.get("conf_threshold", self._conf))
        self._iou = float(config.get("iou_threshold", self._iou))
        self._imgsz = int(config.get("imgsz", self._imgsz))

    async def infer(self, frame: Any) -> list[Detection]:
        assert self._model is not None
        results = self._model.predict(
            frame,
            conf=self._conf,
            iou=self._iou,
            imgsz=self._imgsz,
            device=self._device,
            verbose=False,
        )
        out: list[Detection] = []
        for r in results:
            h, w = r.orig_shape
            for box in r.boxes:
                x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
                out.append(
                    Detection(
                        label=r.names[int(box.cls)],
                        confidence=float(box.conf),
                        bbox=(x1 / w, y1 / h, x2 / w, y2 / h),
                    )
                )
        return out

    async def unload(self) -> None:
        self._model = None
        self._mv_id = None

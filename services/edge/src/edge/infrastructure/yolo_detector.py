import contextlib
import threading
from pathlib import Path

import numpy as np

from edge.domain.detection import Detection


class YoloDetector:
    def __init__(self, weights: Path, imgsz: int, conf: float, torch_threads: int = 1, device: str = "cpu") -> None:
        import torch
        from ultralytics import YOLO  # heavy import, only when the runtime really starts

        self._model = YOLO(str(weights))
        self._imgsz, self._conf, self._device = imgsz, conf, device
        # A GPU model (and a TensorRT engine) is not safe to call from several threads at once, so the cameras take turns.
        # On a CPU every camera thread runs its own inference on its own core, so there is nothing to serialise.
        self._guard = threading.Lock() if device.startswith("cuda") else contextlib.nullcontext()
        self._half = device.startswith("cuda")  # half precision: about twice as fast on a GPU, no change on a CPU
        # The first predict() selects the device, and Ultralytics then resets torch to up to 8 threads (it took 7.5 cores
        # for two cameras). Do it now, on a dummy frame, so that the limit below is the last word.
        self._model.predict(np.zeros((64, 64, 3), np.uint8), imgsz=imgsz, device=device, half=self._half, verbose=False)
        # One thread per inference: every camera detects in its own thread, so more threads inside one inference only
        # make them fight for the cores (measured: 2 threads are slower than 1 for the nano model)
        torch.set_num_threads(torch_threads)

    def detect(self, image: np.ndarray) -> list[Detection]:
        return self.detect_batch([image])[0]

    def detect_batch(self, images: list[np.ndarray]) -> list[list[Detection]]:
        """One model call for all the frames: one list of detections per frame, in the same order."""
        with self._guard:
            results = self._model.predict(images, imgsz=self._imgsz, conf=self._conf, device=self._device, half=self._half, verbose=False)
        return [
            [Detection(r.names[int(b.cls)], float(b.conf), tuple(int(v) for v in b.xyxy[0].tolist())) for b in r.boxes]
            for r in results
        ]

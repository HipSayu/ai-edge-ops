"""NVIDIA DeepStream engine — one GStreamer pipeline does capture + TensorRT
inference + hardware encode for every camera on the device.

    nvurisrcbin(s) ─► nvstreammux ─► nvinfer ─► nvtracker ─► tee
        ├─► pad probe: NvDsBatchMeta -> BboxFramePayload / ViolationPayload
        └─► nvvideoconvert ─► nvv4l2h264enc ─► whip sink (per camera)

Selected by :class:`vision_runtime.core.worker.VisionWorker` when ``RUNTIME=deepstream``
(the model image was built ``FROM nvcr.io/nvidia/deepstream``). On every other
image the CPU pipeline (:mod:`vision_runtime.core.pipeline`) runs.

Status: skeleton. The pipeline construction + ``NvDsBatchMeta`` pad probe are
implemented against a real Jetson / dGPU target (DeepStream 9.1, JetPack 7.2 or
CUDA 13.2) — see ``inference/package/DeepStream``.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

import edge_protocol as p
from dqh.svc_core.contracts.messaging import Envelope

from vision_runtime.config import WorkerSettings

logger = logging.getLogger("vision_runtime.deepstream")

Emit = Callable[[Envelope], Awaitable[None]]


class DeepStreamEngine:
    def __init__(self, settings: WorkerSettings, *, emit: Emit) -> None:
        try:
            import pyds  # noqa: F401, PLC0415
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "DeepStreamEngine needs the DeepStream Python bindings (pyds); run "
                "the gpu model image, or set RUNTIME=onnx"
            ) from exc
        self._settings = settings
        self._emit = emit
        self._cameras: list[p.IpcCameraSpec] = []
        self._pipeline = None

    async def set_cameras(self, cameras: list[p.IpcCameraSpec]) -> None:
        self._cameras = cameras
        raise NotImplementedError(
            "DeepStreamEngine.set_cameras: build the GStreamer pipeline on a real "
            "Jetson/dGPU target — see this module's docstring"
        )

    async def start(self) -> None: ...

    async def stop(self) -> None:
        if self._pipeline is not None:
            import gi  # noqa: PLC0415

            gi.require_version("Gst", "1.0")
            from gi.repository import Gst  # noqa: PLC0415

            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None

    def health(self) -> list[p.CameraHealth]:
        return [
            p.CameraHealth(id=c.id, running=False, detail="deepstream skeleton")
            for c in self._cameras
        ]


__all__ = ["DeepStreamEngine"]

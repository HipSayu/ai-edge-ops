"""NVIDIA DeepStream backend — one GStreamer pipeline does capture + TensorRT
inference + hardware encode for every camera on the device.

    nvurisrcbin(s) ─► nvstreammux ─► nvinfer ─► nvtracker ─► tee
        ├─► pad probe: NvDsBatchMeta -> BboxFramePayload / ViolationPayload
        └─► nvvideoconvert ─► nvv4l2h264enc ─► whip sink (per camera)

Only importable where the DeepStream Python bindings (``pyds``) and CUDA are
present — the boot probe in :mod:`edge_agent.core.hardware` guarantees this
backend is only selected there. On every other device the agent falls back
to :class:`edge_agent.services.backend.ComposedBackend`.

Status: skeleton. The GStreamer pipeline construction and the ``NvDsBatchMeta``
pad probe are implemented against a real Jetson / dGPU target (needs
DeepStream 9.1, JetPack 7.2 or CUDA 13.2). See
``backend/edge_agent/package/DeepStream/skills/deepstream-generate-pipeline``.
"""

from __future__ import annotations

import logging

from edge_agent.core.config import AgentSettings
from edge_agent.core.hardware import Hardware
from edge_agent.network.link import EdgeLink
from edge_agent.runtime import InferenceRuntime
from edge_agent.services.backend import VisionBackend
from edge_agent.services.evidence import EvidenceUploader

logger = logging.getLogger("edge_agent.services.deepstream")


class DeepStreamBackend(VisionBackend):
    def __init__(
        self,
        settings: AgentSettings,
        *,
        hw: Hardware,
        runtime: InferenceRuntime,
        link: EdgeLink,
        evidence_uploader: EvidenceUploader | None = None,
    ) -> None:
        try:
            import pyds  # noqa: F401, PLC0415
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "DeepStreamBackend requires the DeepStream Python bindings (pyds); "
                "run inside an nvcr.io/nvidia/deepstream image or set VISION__BACKEND=composed"
            ) from exc
        self._settings = settings
        self._hw = hw
        self._runtime = runtime
        self._link = link
        self._evidence = evidence_uploader
        self._loop = None
        self._pipeline = None

    async def start(self) -> None:
        raise NotImplementedError(
            "DeepStreamBackend.start: build the GStreamer pipeline on a real "
            "Jetson/dGPU target — see this module's docstring"
        )

    async def stop(self) -> None:
        if self._pipeline is not None:
            import gi  # noqa: PLC0415

            gi.require_version("Gst", "1.0")
            from gi.repository import Gst  # noqa: PLC0415

            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None


__all__ = ["DeepStreamBackend"]

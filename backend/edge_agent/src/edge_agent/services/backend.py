"""VisionBackend — the seam between the agent core and *how* a device turns
cameras into detections + published video.

``ComposedBackend`` is today's design: a cv2 frame loop feeding an
:class:`~edge_agent.runtime.base.InferenceRuntime`, plus a separate ffmpeg
process per camera publishing raw video over WHIP. It runs on anything —
x86 CPU, Raspberry Pi, Apple Silicon, or a Jetson in CPU/ONNX mode.

``deepstream`` (see :mod:`edge_agent.services.deepstream_backend`) fuses
capture + inference + encode into one GStreamer pipeline on NVIDIA GPUs.

The agent core (``EdgeLink``, ``Agent``, the MQTT protocol) never knows
which backend is running — it only receives ``BboxFramePayload`` /
``ViolationPayload``.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from edge_agent.core.config import AgentSettings
from edge_agent.core.hardware import Hardware
from edge_agent.network.link import EdgeLink
from edge_agent.runtime import InferenceRuntime
from edge_agent.services.evidence import EvidenceUploader
from edge_agent.services.pipeline import CameraPipeline
from edge_agent.streaming import VideoPublisher, build_publisher

logger = logging.getLogger("edge_agent.services.backend")


class VisionBackend(ABC):
    """Owns every camera on the device: inference output + published video."""

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...


class ComposedBackend(VisionBackend):
    def __init__(
        self,
        settings: AgentSettings,
        *,
        hw: Hardware,
        runtime: InferenceRuntime,
        link: EdgeLink,
        evidence_uploader: EvidenceUploader | None = None,
    ) -> None:
        self._settings = settings
        self._hw = hw
        self._runtime = runtime
        self._link = link
        self._evidence = evidence_uploader
        self._pipelines: list[CameraPipeline] = []
        self._publishers: list[VideoPublisher] = []

    async def start(self) -> None:
        for cam in self._settings.cameras:
            if not cam.enabled:
                continue
            pipeline = CameraPipeline(
                cam,
                runtime=self._runtime,
                inference=self._settings.inference,
                on_violation=self._link.send_violation,
                device_id=self._settings.device_id,
                evidence_uploader=self._evidence,
                on_bbox_frame=self._link.send_bbox_frame,
            )
            pipeline.start()
            self._pipelines.append(pipeline)

        await self._start_camera_streams()

    async def _start_camera_streams(self) -> None:
        """Dial each enabled, mapped camera out to MediaMTX over WHIP.

        A raw ffmpeg process per camera, reading straight from the device and
        independent of the inference loop. Best-effort: one camera that fails
        to start streaming doesn't stop inference/violation reporting for it.
        The publish token is requested over the existing (already
        authenticated) MQTT link, not a fresh HTTP call.
        """
        if not self._settings.streaming.enabled:
            return
        # Prefer whatever the boot probe already found over re-shelling ffmpeg.
        encoder_pref = self._settings.streaming.encoder
        if encoder_pref == "auto" and self._hw.encoders:
            encoder_pref = next(
                (e for e in ("nvenc", "vaapi", "v4l2m2m") if e in self._hw.encoders),
                "auto",
            )
        for cam in self._settings.cameras:
            if not cam.enabled:
                continue
            if cam.camera_id is None:
                logger.warning("camera %s has no camera_id mapped; skipping stream", cam.id)
                continue
            try:
                token = await self._link.request_stream_token(
                    cam.camera_id, timeout=self._settings.server.request_timeout_s
                )
                publisher = build_publisher(
                    self._settings.streaming.kind,
                    encoder=encoder_pref,
                    bitrate_kbps=self._settings.streaming.bitrate_kbps,
                )
                await publisher.start(
                    source=cam.source,
                    whip_url=token.url,
                    token=token.token,
                    loop=cam.loop,
                )
                self._publishers.append(publisher)
            except Exception:  # noqa: BLE001 - one bad camera shouldn't block the rest
                logger.exception("could not start stream for camera %s", cam.id)

    async def stop(self) -> None:
        for publisher in self._publishers:
            await publisher.stop()
        self._publishers.clear()
        for pipeline in self._pipelines:
            await pipeline.stop()
        self._pipelines.clear()


def build_backend(
    kind: str,
    settings: AgentSettings,
    *,
    hw: Hardware,
    runtime: InferenceRuntime,
    link: EdgeLink,
    evidence_uploader: EvidenceUploader | None = None,
) -> VisionBackend:
    if kind == "deepstream":
        from edge_agent.services.deepstream_backend import DeepStreamBackend

        return DeepStreamBackend(
            settings, hw=hw, runtime=runtime, link=link, evidence_uploader=evidence_uploader
        )
    return ComposedBackend(
        settings, hw=hw, runtime=runtime, link=link, evidence_uploader=evidence_uploader
    )


__all__ = ["ComposedBackend", "VisionBackend", "build_backend"]

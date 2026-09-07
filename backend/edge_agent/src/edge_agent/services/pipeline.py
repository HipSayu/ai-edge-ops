"""Camera -> runtime -> PPE rule -> violation event."""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
from collections.abc import Awaitable, Callable

import edge_protocol as p

from edge_agent.analytics.ppe import evaluate_ppe
from edge_agent.core.config import CameraConfig, InferenceConfig
from edge_agent.runtime import Detection, InferenceRuntime
from edge_agent.services.evidence import EvidenceUploader
from edge_agent.utils.video import frames

logger = logging.getLogger("edge_agent.services.pipeline")

ViolationSink = Callable[[p.ViolationPayload], Awaitable[None]]
BboxSink = Callable[[p.BboxFramePayload], Awaitable[None]]


class CameraPipeline:
    def __init__(
        self,
        camera: CameraConfig,
        *,
        runtime: InferenceRuntime,
        inference: InferenceConfig,
        on_violation: ViolationSink,
        device_id: str = "unknown",
        evidence_uploader: EvidenceUploader | None = None,
        min_gap_s: float = 10.0,
        on_bbox_frame: BboxSink | None = None,
    ) -> None:
        self.camera = camera
        self.runtime = runtime
        self.inference = inference
        self._sink = on_violation
        self.device_id = device_id
        self._evidence_uploader = evidence_uploader
        self._min_gap = min_gap_s
        self._last_sent: dict[str, dt.datetime] = {}
        self._bbox_sink = on_bbox_frame
        self._bbox_seq = 0
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name=f"pipeline-{self.camera.id}")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run(self) -> None:
        delay = 1.0 / max(self.camera.fps_limit, 0.1)
        for frame in frames(self.camera.source, loop=self.camera.loop):
            if not self.runtime.loaded:
                await asyncio.sleep(delay)
                continue
            try:
                detections = await self.runtime.infer(frame)
                await self._emit_bbox_frame(detections)
                for vtype in evaluate_ppe(detections, self.inference.ppe_required):
                    await self._emit(vtype, detections, frame)
            except Exception:  # noqa: BLE001
                logger.exception("pipeline %s inference error", self.camera.id)
            await asyncio.sleep(delay)

    async def _emit_bbox_frame(self, detections: list[Detection]) -> None:
        if self._bbox_sink is None:
            return
        self._bbox_seq += 1
        # Epoch seconds: the frontend pairs this against the WHEP video frame
        # it's currently displaying by nearest wall-clock timestamp, since the
        # two travel over independent transports (MQTT vs WebRTC/RTP).
        frame_ts = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        await self._bbox_sink(
            p.BboxFramePayload(
                camera_id=self.camera.id,
                frame_ts=frame_ts,
                seq=self._bbox_seq,
                detections=[
                    p.BboxPayload(label=d.label, confidence=d.confidence, bbox=d.bbox)
                    for d in detections
                ],
            )
        )

    async def _emit(self, vtype: str, detections: list[Detection], frame: object) -> None:
        now = dt.datetime.now(tz=dt.timezone.utc)
        if (last := self._last_sent.get(vtype)) and (now - last).total_seconds() < self._min_gap:
            return
        self._last_sent[vtype] = now
        conf = max((d.confidence for d in detections if d.label.startswith("no_")), default=0.9)
        image_path = None
        if self._evidence_uploader is not None:
            try:
                image_path = await self._evidence_uploader.upload(
                    frame,
                    device_id=self.device_id,
                    camera_id=self.camera.id,
                    violation_type=vtype,
                    recorded_at=now,
                )
            except Exception:  # noqa: BLE001 - event delivery must continue without evidence
                logger.exception("evidence upload failed for camera %s", self.camera.id)
        await self._sink(
            p.ViolationPayload(
                zone=self.camera.zone,
                violation_type=vtype,
                confidence=conf,
                image_path=image_path,
                recorded_at=now,
            )
        )

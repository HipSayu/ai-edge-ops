"""One camera: capture -> runtime.infer -> emit bbox frame -> PPE rule -> violation.

Emits are `edge_protocol.Envelope`s pushed to the agent over the IPC channel.
Video (WHIP) is a separate concern — see :mod:`vision_runtime.publishers`.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
from collections.abc import Awaitable, Callable

import edge_protocol as p
from dqh.svc_core.contracts.messaging import Envelope

from vision_runtime.capture.frame_source import frames
from vision_runtime.config import InferenceConfig
from vision_runtime.core.evidence import EvidenceUploader
from vision_runtime.rules.ppe import evaluate_ppe
from vision_runtime.runtime import Detection, InferenceRuntime

logger = logging.getLogger("vision_runtime.core.pipeline")

Emit = Callable[[Envelope], Awaitable[None]]


class CameraPipeline:
    def __init__(
        self,
        camera: p.IpcCameraSpec,
        *,
        runtime: InferenceRuntime,
        inference: InferenceConfig,
        emit: Emit,
        device_id: str = "unknown",
        evidence: EvidenceUploader | None = None,
        min_gap_s: float = 10.0,
    ) -> None:
        self.camera = camera
        self.runtime = runtime
        self.inference = inference
        self._emit = emit
        self._device_id = device_id
        self._evidence = evidence
        self._min_gap = min_gap_s
        self._last_sent: dict[str, dt.datetime] = {}
        self._seq = 0
        self._task: asyncio.Task[None] | None = None
        self._frames = 0
        self._last_frame_at: dt.datetime | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name=f"pipeline-{self.camera.id}")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def health(self) -> p.CameraHealth:
        age = None
        if self._last_frame_at is not None:
            age = (dt.datetime.now(dt.timezone.utc) - self._last_frame_at).total_seconds()
        return p.CameraHealth(id=self.camera.id, running=self.running, last_frame_age_s=age)

    async def _run(self) -> None:
        delay = 1.0 / max(self.camera.fps_limit, 0.1)
        gen = frames(self.camera.source, loop=self.camera.loop)  # blocking (cv2) generator
        while True:
            frame = await asyncio.to_thread(_next, gen)
            if frame is _DONE:
                break
            if not self.runtime.loaded:
                await asyncio.sleep(delay)
                continue
            try:
                detections = await self.runtime.infer(frame)
                await self._emit_bbox(detections)
                for vtype in evaluate_ppe(detections, self.inference.ppe_required):
                    await self._emit_violation(vtype, detections, frame)
            except Exception:  # noqa: BLE001
                logger.exception("pipeline %s inference error", self.camera.id)
            self._frames += 1
            self._last_frame_at = dt.datetime.now(dt.timezone.utc)
            await asyncio.sleep(delay)

    async def _emit_bbox(self, detections: list[Detection]) -> None:
        self._seq += 1
        await self._send(
            p.T_BBOX_FRAME,
            p.BboxFramePayload(
                camera_id=self.camera.id,
                frame_ts=dt.datetime.now(dt.timezone.utc).timestamp(),
                seq=self._seq,
                detections=[
                    p.BboxPayload(label=d.label, confidence=d.confidence, bbox=d.bbox)
                    for d in detections
                ],
            ),
        )

    async def _emit_violation(self, vtype: str, detections: list[Detection], frame: object) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        last = self._last_sent.get(vtype)
        if last and (now - last).total_seconds() < self._min_gap:
            return
        self._last_sent[vtype] = now
        conf = max((d.confidence for d in detections if d.label.startswith("no_")), default=0.9)
        image_path = None
        if self._evidence is not None:
            try:
                image_path = await self._evidence.upload(
                    frame,
                    device_id=self._device_id,
                    camera_id=self.camera.id,
                    violation_type=vtype,
                    recorded_at=now,
                )
            except Exception:  # noqa: BLE001 - event delivery continues without evidence
                logger.exception("evidence upload failed for camera %s", self.camera.id)
        await self._send(
            p.T_VIOLATION,
            p.ViolationPayload(
                zone=self.camera.zone,
                violation_type=vtype,
                confidence=conf,
                image_path=image_path,
                recorded_at=now,
            ),
        )

    async def _send(self, type_: str, payload) -> None:
        await self._emit(
            Envelope(type=type_, source=self.camera.id, payload=payload.model_dump(mode="json"))
        )


_DONE = object()


def _next(gen):
    try:
        return next(gen)
    except StopIteration:
        return _DONE


__all__ = ["CameraPipeline"]

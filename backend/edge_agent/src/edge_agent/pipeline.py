"""Camera -> runtime -> PPE rule -> violation event."""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
from collections.abc import Awaitable, Callable

import edge_protocol as p

from edge_agent.config import CameraConfig, InferenceConfig
from edge_agent.runtime import Detection, InferenceRuntime

logger = logging.getLogger("edge_agent.pipeline")

ViolationSink = Callable[[p.ViolationPayload], Awaitable[None]]


def _frames(source: str):
    """Yield frames. Uses OpenCV if available, else ``None`` placeholders."""
    try:
        import cv2  # noqa: PLC0415
    except ModuleNotFoundError:
        while True:
            yield None
        return
    cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            yield frame
    finally:
        cap.release()


def evaluate_ppe(detections: list[Detection], required: list[str]) -> list[str]:
    """Return the list of violation types (e.g. ``["no_helmet"]``)."""
    if not any(d.label == "person" for d in detections):
        return []
    present = {d.label for d in detections}
    violations = [f"no_{item}" for item in required if item not in present]
    violations += [d.label for d in detections if d.label.startswith("no_")]
    return sorted(set(violations))


class CameraPipeline:
    def __init__(
        self,
        camera: CameraConfig,
        *,
        runtime: InferenceRuntime,
        inference: InferenceConfig,
        on_violation: ViolationSink,
        min_gap_s: float = 10.0,
    ) -> None:
        self.camera = camera
        self.runtime = runtime
        self.inference = inference
        self._sink = on_violation
        self._min_gap = min_gap_s
        self._last_sent: dict[str, dt.datetime] = {}
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name=f"pipeline-{self.camera.id}")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run(self) -> None:
        delay = 1.0 / max(self.camera.fps_limit, 0.1)
        for frame in _frames(self.camera.source):
            if not self.runtime.loaded:
                await asyncio.sleep(delay)
                continue
            try:
                detections = await self.runtime.infer(frame)
                for vtype in evaluate_ppe(detections, self.inference.ppe_required):
                    await self._emit(vtype, detections)
            except Exception:  # noqa: BLE001
                logger.exception("pipeline %s inference error", self.camera.id)
            await asyncio.sleep(delay)

    async def _emit(self, vtype: str, detections: list[Detection]) -> None:
        now = dt.datetime.now(tz=dt.timezone.utc)
        if (last := self._last_sent.get(vtype)) and (now - last).total_seconds() < self._min_gap:
            return
        self._last_sent[vtype] = now
        conf = max((d.confidence for d in detections if d.label.startswith("no_")), default=0.9)
        await self._sink(
            p.ViolationPayload(
                zone=self.camera.zone,
                violation_type=vtype,
                confidence=conf,
                recorded_at=now,
            )
        )

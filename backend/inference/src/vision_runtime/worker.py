"""VisionWorker — owns cameras, runs the inference pipelines and WHIP publishers,
and speaks the agent IPC channel.

Lifecycle: connect -> HELLO -> wait for SET_CAMERAS -> run pipelines -> stream
health. Video tokens are requested from the agent over the same channel (the
agent holds the MQTT identity; the worker has no control-plane credential).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging

import edge_protocol as p
from dqh.svc_core.contracts.messaging import Envelope
from edge_protocol.channel import MessageChannel

from vision_runtime.config import InferenceConfig, WorkerSettings
from vision_runtime.evidence import HttpEvidenceUploader
from vision_runtime.pipeline import CameraPipeline
from vision_runtime.publish import build_publisher
from vision_runtime.runtime import build_runtime

logger = logging.getLogger("vision_runtime.worker")


class VisionWorker:
    def __init__(self, settings: WorkerSettings, channel: MessageChannel) -> None:
        self._settings = settings
        self._ch = channel
        self._runtime = build_runtime(settings.runtime, device=_resolve_device(settings.device))
        self._pipelines: dict[str, CameraPipeline] = {}
        self._publishers: dict[str, object] = {}
        self._device_id = "unknown"
        self._token_waiters: dict[str, asyncio.Future] = {}
        self._tasks: list[asyncio.Task] = []
        self._stop = asyncio.Event()

    async def run(self) -> None:
        await self._load_model()
        await self._send(p.T_VR_HELLO, {"model_version_id": self._settings.model_version_id})
        self._tasks.append(asyncio.create_task(self._health_loop(), name="vr-health"))
        try:
            async for env in self._ch.messages():
                await self._on_message(env)
        finally:
            await self.stop()

    async def stop(self) -> None:
        self._stop.set()
        for t in self._tasks:
            t.cancel()
        for pipe in self._pipelines.values():
            await pipe.stop()
        for pub in self._publishers.values():
            with contextlib.suppress(Exception):
                await pub.stop()  # type: ignore[attr-defined]
        await self._runtime.unload()

    # --- inbound ---------------------------------------------------
    async def _on_message(self, env: Envelope) -> None:
        if env.type == p.T_VR_SET_CAMERAS:
            await self._apply_cameras(p.SetCamerasPayload.model_validate(env.payload))
        elif env.type == p.T_VR_STREAM_TOKEN:
            reply = p.StreamTokenReplyPayload.model_validate(env.payload)
            fut = self._token_waiters.pop(reply.path, None)
            if fut and not fut.done():
                fut.set_result(reply)
        else:
            logger.debug("ignoring message type %s", env.type)

    async def _apply_cameras(self, spec: p.SetCamerasPayload) -> None:
        inference = InferenceConfig(
            weights_dir=self._settings.inference.weights_dir,
            conf_threshold=spec.conf_threshold,
            iou_threshold=spec.iou_threshold,
            imgsz=spec.imgsz,
            ppe_required=spec.ppe_required,
        )
        evidence = (
            HttpEvidenceUploader(spec.evidence_url, token=spec.evidence_token)
            if spec.evidence_url
            else None
        )
        wanted = {c.id: c for c in spec.cameras if c.enabled}

        for cam_id in list(self._pipelines):
            if cam_id not in wanted:
                await self._pipelines.pop(cam_id).stop()
                await self._stop_publisher(cam_id)

        for cam_id, cam in wanted.items():
            if cam_id in self._pipelines:
                continue
            pipe = CameraPipeline(
                cam,
                runtime=self._runtime,
                inference=inference,
                emit=self._send_envelope,
                device_id=self._device_id,
                evidence=evidence,
                min_gap_s=self._settings.min_violation_gap_s,
            )
            pipe.start()
            self._pipelines[cam_id] = pipe
            if spec.streaming_enabled and cam.camera_id is not None:
                self._tasks.append(
                    asyncio.create_task(
                        self._start_stream(cam, spec.encoder, spec.bitrate_kbps),
                        name=f"vr-stream-{cam_id}",
                    )
                )

    # --- streaming ------------------------------------------------
    async def _start_stream(self, cam: p.IpcCameraSpec, encoder: str, bitrate: int) -> None:
        try:
            token = await self._request_token(cam.camera_id)
            publisher = build_publisher("ffmpeg", encoder=encoder, bitrate_kbps=bitrate)
            await publisher.start(
                source=cam.source, whip_url=token.url, token=token.token, loop=cam.loop
            )
            self._publishers[cam.id] = publisher
        except Exception:  # noqa: BLE001
            logger.exception("could not start stream for camera %s", cam.id)

    async def _request_token(self, camera_id: int) -> p.StreamTokenReplyPayload:
        path = f"cam_{camera_id}"
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._token_waiters[path] = fut
        await self._send(
            p.T_STREAM_TOKEN_REQUEST,
            p.StreamTokenRequestPayload(camera_id=camera_id).model_dump(mode="json"),
        )
        return await asyncio.wait_for(fut, timeout=15.0)

    async def _stop_publisher(self, cam_id: str) -> None:
        pub = self._publishers.pop(cam_id, None)
        if pub is not None:
            with contextlib.suppress(Exception):
                await pub.stop()  # type: ignore[attr-defined]

    # --- model ---------------------------------------------------
    async def _load_model(self) -> None:
        weights = _find_weights(self._settings.inference.weights_dir)
        try:
            await self._runtime.load(
                weights_path=weights,
                model_version_id=self._settings.model_version_id or 0,
                config=self._settings.inference.model_dump(),
            )
        except Exception:  # noqa: BLE001
            logger.exception("model load failed (weights=%s)", weights)

    # --- outbound ----------------------------------------------
    async def _send(self, type_: str, payload: dict) -> None:
        await self._ch.send(Envelope(type=type_, source="vision-runtime", payload=payload))

    async def _send_envelope(self, env: Envelope) -> None:
        await self._ch.send(env)

    async def _health_loop(self) -> None:
        while not self._stop.is_set():
            await asyncio.sleep(self._settings.health_interval_s)
            cams = [pipe.health() for pipe in self._pipelines.values()]
            for h in cams:
                h.streaming = h.id in self._publishers
            await self._send(
                p.T_VR_HEALTH,
                p.WorkerHealthPayload(
                    model_version=self._runtime.model_version_id, cameras=cams
                ).model_dump(mode="json"),
            )


def _resolve_device(device: str) -> str:
    """``auto`` -> probe the hardware: CUDA, then Apple MPS, else CPU. One
    multi-arch model image runs everywhere; the runtime picks the accelerator."""
    if device != "auto":
        return device
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda:0"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except ModuleNotFoundError:
        pass
    return "cpu"


def _find_weights(weights_dir: str) -> str:
    from pathlib import Path

    root = Path(weights_dir)
    for pattern in ("*.engine", "*.onnx", "*.pt", "*.tflite"):
        found = sorted(root.glob(pattern))
        if found:
            return str(found[0])
    return str(root / "model.onnx")  # let the runtime raise a clear error


__all__ = ["VisionWorker"]

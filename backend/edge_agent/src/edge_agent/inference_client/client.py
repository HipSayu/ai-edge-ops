"""Bridge the vision-runtime container to the MQTT link.

The runtime container does capture + inference + the PPE rule + WHIP publish, and
emits everything over the IPC channel. This client:

* forwards ``T_BBOX_FRAME`` / ``T_VIOLATION`` straight to :class:`EdgeLink`
* answers ``T_STREAM_TOKEN_REQUEST`` by doing the MQTT RPC on the runtime's behalf
* tracks the last ``T_VR_HEALTH`` for the local status API
* pushes ``T_VR_SET_CAMERAS`` whenever it (re)connects

The agent holds the one MQTT identity; the runtime never talks to the broker.
"""

from __future__ import annotations

import asyncio
import logging

import edge_protocol as p
from dqh.svc_core.contracts.messaging import Envelope
from edge_protocol.channel import MessageChannel, UnixSocketChannel

from edge_agent.core.config import AgentSettings
from edge_agent.network.link import EdgeLink

logger = logging.getLogger("edge_agent.inference_client")


class InferenceClient:
    def __init__(self, settings: AgentSettings, link: EdgeLink) -> None:
        self._settings = settings
        self._link = link
        self._channel: MessageChannel | None = None
        self._task: asyncio.Task[None] | None = None
        self.last_health: p.WorkerHealthPayload | None = None
        self.connected = False

    async def start(self) -> None:
        self._task = asyncio.create_task(self._connect_loop(), name="inference-client")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None
        if self._channel:
            await self._channel.aclose()

    # --- connection ------------------------------------------------
    async def _connect_loop(self) -> None:
        path = self._settings.inference_socket
        while True:
            try:
                self._channel = await UnixSocketChannel.connect(path)
                self.connected = True
                logger.info("connected to vision-runtime (%s)", path)
                await self._send_cameras()
                async for env in self._channel.messages():
                    await self._on_message(env)
            except (ConnectionError, FileNotFoundError, OSError) as exc:
                logger.warning("vision-runtime link down (%s); retrying", exc)
            finally:
                self.connected = False
            await asyncio.sleep(3.0)

    async def _send_cameras(self) -> None:
        if self._channel is None:
            return
        s = self._settings
        payload = p.SetCamerasPayload(
            cameras=[p.IpcCameraSpec(**c.model_dump()) for c in s.cameras],
            evidence_url=s.server.base_url,
            evidence_token=s.server.enroll_token,
            streaming_enabled=s.streaming_enabled,
            encoder=s.streaming_encoder,
            bitrate_kbps=s.streaming_bitrate_kbps,
        )
        await self._channel.send(
            Envelope(
                type=p.T_VR_SET_CAMERAS,
                source="agent",
                payload=payload.model_dump(mode="json"),
            )
        )

    # --- inbound from the runtime --------------------------------
    async def _on_message(self, env: Envelope) -> None:
        if env.type == p.T_BBOX_FRAME:
            await self._link.send_bbox_frame(p.BboxFramePayload.model_validate(env.payload))
        elif env.type == p.T_VIOLATION:
            await self._link.send_violation(p.ViolationPayload.model_validate(env.payload))
        elif env.type == p.T_STREAM_TOKEN_REQUEST:
            await self._issue_token(p.StreamTokenRequestPayload.model_validate(env.payload))
        elif env.type == p.T_VR_HEALTH:
            self.last_health = p.WorkerHealthPayload.model_validate(env.payload)
        elif env.type == p.T_VR_HELLO:
            logger.info("vision-runtime hello: %s", env.payload)

    async def _issue_token(self, req: p.StreamTokenRequestPayload) -> None:
        if self._channel is None:
            return
        try:
            reply = await self._link.request_stream_token(req.camera_id)
        except Exception:  # noqa: BLE001
            logger.exception("stream token RPC failed for camera %s", req.camera_id)
            return
        await self._channel.send(
            Envelope(
                type=p.T_VR_STREAM_TOKEN,
                source="agent",
                payload=reply.model_dump(mode="json"),
            )
        )


__all__ = ["InferenceClient"]

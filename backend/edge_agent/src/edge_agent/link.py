"""MQTT link to the control plane: heartbeats out, commands in, acks back."""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import traceback
from collections.abc import Awaitable, Callable

import edge_protocol as p
from dqh.svc_core.messaging import Envelope, MessageBus
from dqh.svc_core.messaging.rpc import RpcClient

from edge_agent.helpers.metrics import collect_metrics

logger = logging.getLogger("edge_agent.link")

CommandHandler = Callable[[Envelope], Awaitable[p.CommandAckPayload]]


class EdgeLink:
    def __init__(
        self,
        bus: MessageBus,
        *,
        device_id: str,
        heartbeat_interval_s: float,
        on_command: CommandHandler,
        heartbeat_extra: Callable[[], p.HeartbeatPayload] | None = None,
    ) -> None:
        self.bus = bus
        self.device_id = device_id
        self._interval = heartbeat_interval_s
        self._on_command = on_command
        self._heartbeat_extra = heartbeat_extra
        self._hb_task: asyncio.Task[None] | None = None
        self._rpc = RpcClient(bus, source=device_id)

    async def start(self) -> None:
        if not self.bus.connected:
            await self.bus.connect()
        # every message on our cmd topic is a command
        await self.bus.subscribe(
            p.TOPIC_CMD.render(device_id=self.device_id), self._handle_command
        )
        self._hb_task = asyncio.create_task(self._heartbeat_loop(), name="edge-heartbeat")
        logger.info("edge link up (device=%s)", self.device_id)

    async def stop(self) -> None:
        if self._hb_task:
            self._hb_task.cancel()
            self._hb_task = None
        await self.bus.aclose()

    # --- outbound ------------------------------------------------------
    async def _publish(self, topic: str, mtype: str, payload) -> None:
        await self.bus.publish(
            topic,
            Envelope(type=mtype, source=self.device_id, payload=payload.model_dump(mode="json")),
        )

    async def send_heartbeat(self, payload: p.HeartbeatPayload) -> None:
        await self._publish(
            p.TOPIC_STATE.render(device_id=self.device_id), p.T_HEARTBEAT, payload
        )

    async def send_violation(self, payload: p.ViolationPayload) -> None:
        await self._publish(
            p.TOPIC_EVENTS.render(device_id=self.device_id), p.T_VIOLATION, payload
        )

    async def send_state(self, payload: p.StateReportPayload) -> None:
        await self._publish(
            p.TOPIC_STATE.render(device_id=self.device_id), p.T_STATE_REPORT, payload
        )

    async def send_log(self, payload: p.LogPayload) -> None:
        await self._publish(
            p.TOPIC_LOGS.render(device_id=self.device_id), p.T_LOG, payload
        )

    async def send_bbox_frame(self, payload: p.BboxFramePayload) -> None:
        await self._publish(
            p.TOPIC_BBOX.render(device_id=self.device_id), p.T_BBOX_FRAME, payload
        )

    async def request_stream_token(
        self, camera_id: int, *, timeout: float = 10.0
    ) -> p.StreamTokenReplyPayload:
        """Ask the server for a short-lived WHIP publish token, over MQTT.

        Reuses this link's existing authentication (TLS client cert /
        username-password on the broker) instead of a separate HTTP call —
        the edge agent has no HTTP credential of its own.
        """
        env = await self._rpc.request(
            p.TOPIC_STREAM_TOKEN.render(device_id=self.device_id),
            p.StreamTokenRequestPayload(camera_id=camera_id).model_dump(mode="json"),
            type=p.T_STREAM_TOKEN_REQUEST,
            timeout=timeout,
        )
        return p.StreamTokenReplyPayload.model_validate(env.payload)

    # --- inbound ------------------------------------------------------
    async def _handle_command(self, env: Envelope) -> None:
        try:
            ack = await self._on_command(env)
        except Exception as exc:  # noqa: BLE001 - always ack, even on failure
            logger.exception("command %s failed", env.type)
            ack = p.CommandAckPayload(command_id=env.id, status="failed", detail=str(exc))
        await self.bus.publish(
            p.TOPIC_ACK.render(device_id=self.device_id),
            Envelope(
                type=p.T_COMMAND_ACK,
                source=self.device_id,
                correlation_id=env.correlation_id or env.id,
                payload=ack.model_dump(mode="json"),
            ),
        )

    async def _heartbeat_loop(self) -> None:
        while True:
            try:
                payload = (self._heartbeat_extra or collect_metrics)()
                await self.send_heartbeat(payload)
            except Exception:  # noqa: BLE001
                logger.exception("heartbeat failed")
            await asyncio.sleep(self._interval)


class MqttLogHandler(logging.Handler):
    """Forward edge log records without blocking the logging caller."""

    def __init__(self, link: EdgeLink) -> None:
        super().__init__()
        self.link = link

    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload = p.LogPayload(
                level=record.levelname,
                logger=record.name,
                message=record.getMessage(),
                recorded_at=dt.datetime.now(dt.timezone.utc),
                exception="".join(traceback.format_exception(*record.exc_info))
                if record.exc_info
                else None,
            )
            task = asyncio.create_task(self.link.send_log(payload))
            task.add_done_callback(self._consume_task_error)
        except Exception:
            self.handleError(record)

    @staticmethod
    def _consume_task_error(task: asyncio.Task[None]) -> None:
        try:
            task.result()
        except Exception:
            pass

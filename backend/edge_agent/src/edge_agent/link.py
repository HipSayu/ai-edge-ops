"""MQTT link to the control plane: heartbeats out, commands in, acks back."""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
from collections.abc import Awaitable, Callable

import edge_protocol as p
import psutil
from dqh.svc_core.messaging import Envelope, MessageBus

logger = logging.getLogger("edge_agent.link")

CommandHandler = Callable[[Envelope], Awaitable[p.CommandAckPayload]]


def _now() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)


def collect_metrics() -> p.HeartbeatPayload:
    temps = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}
    temp = next((s.current for group in temps.values() for s in group), None)
    return p.HeartbeatPayload(
        cpu_percent=psutil.cpu_percent(interval=None),
        mem_percent=psutil.virtual_memory().percent,
        temperature_c=temp,
        recorded_at=_now(),
    )


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

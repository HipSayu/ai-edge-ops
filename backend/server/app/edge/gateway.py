"""AgentGateway — the server end of the edge protocol.

Binds a :class:`dqh.svc_core.messaging.MessageBus` to the existing application
services. Transport choice (in-memory / MQTT / ...) is the caller's; the gateway
only speaks the port.
"""

from __future__ import annotations

import datetime as dt
import logging
from uuid import uuid4

import edge_protocol as protocol
from dqh.svc_core.contracts.messaging import Envelope, MessageBus, Subscription
from dqh.svc_core.messaging import MessageRouter
from dqh.svc_core.messaging.rpc import RpcServer

from app.core import database
from app.core.events import event_bus
from app.core.fleet import fleet
from app.core.ws import ws_hub
from app.modules.agent import AgentService
from app.modules.agent.event import DeviceWentOffline
from app.modules.agent.schemas import HeartbeatIn
from app.modules.agent.telemetry_relay import publish_sample
from app.modules.deployment.event import ConfigResolved, DeploymentFailed, DeployRequested
from app.modules.streaming.service import StreamingService
from app.shared.helpers.protocol import device_id_from_envelope

logger = logging.getLogger("app.edge.gateway")


class AgentGateway:
    def __init__(self, bus: MessageBus, *, session_factory=None) -> None:
        self.bus = bus
        self._session_factory = session_factory
        self.router = MessageRouter()
        self._subs: list[Subscription] = []
        self._rpc = RpcServer(bus, source="server")
        # device_id -> monotonic-ish ts of the last telemetry sample persisted;
        # fast telemetry fans out live but only lands in the DB once a minute.
        self._telemetry_persisted_at: dict[str, dt.datetime] = {}
        self._telemetry_persist_gap = dt.timedelta(seconds=60)

    def _session(self):
        """Resolve the session factory at call time (tests swap the module global)."""
        return (self._session_factory or database.async_session)()

    async def start(self) -> None:
        self.router.on(protocol.T_HEARTBEAT, self._on_heartbeat)
        self.router.on(protocol.T_TELEMETRY, self._on_telemetry)
        self.router.on(protocol.T_STATE_REPORT, self._on_state_report)
        self.router.on(protocol.T_LOG, self._on_log)
        self.router.on(protocol.T_BBOX_FRAME, self._on_bbox_frame)
        for pattern in (
            protocol.SUB_STATE,
            protocol.SUB_TELEMETRY,
            protocol.SUB_EVENTS,
            protocol.SUB_LOGS,
            protocol.SUB_BBOX,
        ):
            self._subs.append(await self.bus.subscribe(pattern, self.router.dispatch))
        self._subs.append(
            await self._rpc.bind(protocol.SUB_STREAM_TOKEN, self._on_stream_token_request)
        )
        event_bus.subscribe(DeployRequested, self._on_deploy_requested)
        event_bus.subscribe(ConfigResolved, self._on_config_resolved)
        logger.info("agent gateway started (bus=%s)", type(self.bus).__name__)

    async def stop(self) -> None:
        for sub in self._subs:
            await sub.unsubscribe()
        self._subs.clear()

    # --- inbound (edge -> server) ---------------------------------------
    async def _on_heartbeat(self, env: Envelope) -> None:
        device_id = device_id_from_envelope(env)
        p = protocol.HeartbeatPayload.model_validate(env.payload)
        caps = p.capabilities
        async with self._session() as session:
            await AgentService(session).record_heartbeat(
                device_id,
                HeartbeatIn(
                    recorded_at=p.recorded_at,
                    cpu_percent=p.cpu_percent,
                    gpu_percent=p.gpu_percent,
                    mem_percent=p.mem_percent,
                    mem_used_mb=p.mem_used_mb,
                    mem_total_mb=p.mem_total_mb,
                    disk_percent=p.disk_percent,
                    temperature_c=p.temperature_c,
                    fps=p.fps,
                    inference_latency_ms=p.inference_latency_ms,
                    agent_version=caps.agent_version if caps else None,
                    ip_address=caps.ip_address if caps else None,
                    uptime_s=caps.uptime_s if caps else None,
                    backend=caps.backend if caps else None,
                    arch=caps.arch if caps else None,
                    active_image=p.active_image,
                ),
            )
        if caps is not None:
            logger.debug(
                "device %s: agent=%s backend=%s device=%s formats=%s",
                device_id,
                caps.agent_version,
                caps.backend,
                caps.device,
                caps.model_formats,
            )

    async def _on_telemetry(self, env: Envelope) -> None:
        """Fast metric stream: fan every sample out to dashboards over WS, but
        only persist one per minute so the history table stays small."""
        device_id = device_id_from_envelope(env)
        payload = protocol.TelemetryPayload.model_validate(env.payload)
        if not payload.samples:
            return
        fleet.record_heartbeat(device_id, payload.samples[-1])

        now = dt.datetime.now(dt.timezone.utc)
        for sample in payload.samples:
            recorded_at = sample.recorded_at or now
            await publish_sample(
                device_id,
                {
                    "recorded_at": recorded_at.isoformat(),
                    "cpu_percent": sample.cpu_percent,
                    "gpu_percent": sample.gpu_percent,
                    "mem_percent": sample.mem_percent,
                    "mem_used_mb": sample.mem_used_mb,
                    "mem_total_mb": sample.mem_total_mb,
                    "disk_percent": sample.disk_percent,
                    "temperature_c": sample.temperature_c,
                    "fps": sample.fps,
                    "inference_latency_ms": sample.inference_latency_ms,
                },
            )

        last_persisted = self._telemetry_persisted_at.get(device_id)
        if last_persisted is None or now - last_persisted >= self._telemetry_persist_gap:
            self._telemetry_persisted_at[device_id] = now
            latest = payload.samples[-1]
            try:
                async with self._session() as session:
                    await AgentService(session).record_heartbeat(
                        device_id,
                        HeartbeatIn(
                            recorded_at=latest.recorded_at,
                            cpu_percent=latest.cpu_percent,
                            gpu_percent=latest.gpu_percent,
                            mem_percent=latest.mem_percent,
                            mem_used_mb=latest.mem_used_mb,
                            mem_total_mb=latest.mem_total_mb,
                            disk_percent=latest.disk_percent,
                            temperature_c=latest.temperature_c,
                            fps=latest.fps,
                            inference_latency_ms=latest.inference_latency_ms,
                        ),
                    )
            except Exception:  # noqa: BLE001 - live fan-out already happened; DB is best-effort
                logger.exception("telemetry downsample-persist failed for device %s", device_id)

    async def _on_state_report(self, env: Envelope) -> None:
        p = protocol.StateReportPayload.model_validate(env.payload)
        fleet.record_state(device_id_from_envelope(env), p)
        logger.debug("state report from %s: %s", env.source, p.runtime_status)

    async def _on_bbox_frame(self, env: Envelope) -> None:
        """Forward detections to the frontend over WS, keyed by camera.

        Video for the same camera arrives at the browser separately, over
        WHEP from MediaMTX — this is metadata-only, paired to the right
        frame client-side via ``frame_ts``.
        """
        payload = protocol.BboxFramePayload.model_validate(env.payload)
        await ws_hub.publish(
            f"bbox/{payload.camera_id}",
            Envelope(
                type=protocol.T_BBOX_FRAME,
                source=env.source,
                payload=payload.model_dump(mode="json"),
            ),
        )

    async def _on_stream_token_request(self, env: Envelope) -> dict:
        """RPC handler: edge asks (over the already-authenticated MQTT link)
        for a WHIP publish token for one of its cameras.

        No separate HTTP device-auth needed — the request only reaches here
        because it arrived on this device's own MQTT topic, which the broker
        already authenticated (TLS client cert / username-password).
        """
        payload = protocol.StreamTokenRequestPayload.model_validate(env.payload)
        token = StreamingService().issue_publish_token(payload.camera_id)
        return protocol.StreamTokenReplyPayload(
            url=token.url, path=token.path, token=token.token, expires_at=token.expires_at
        ).model_dump(mode="json")

    async def _on_log(self, env: Envelope) -> None:
        payload = protocol.LogPayload.model_validate(env.payload)
        await ws_hub.publish(
            f"logs/{env.source}",
            Envelope(
                type=protocol.T_LOG,
                source=env.source,
                payload={
                    "device_id": env.source,
                    **payload.model_dump(mode="json"),
                },
            ),
        )

    # --- outbound (server -> edge) -------------------------------------
    async def _on_deploy_requested(self, event: DeployRequested) -> None:
        if not event.image:
            await event_bus.publish(
                DeploymentFailed(device_id=event.device_id, reason="no model image")
            )
            return
        payload = protocol.DeployModelPayload(
            command_id=uuid4().hex,
            deployment_id=0,
            image=event.image,
            config=dict(event.config),
        )
        await self.send_command(event.device_id, protocol.T_DEPLOY_MODEL, payload)

    async def _on_config_resolved(self, event: ConfigResolved) -> None:
        payload = protocol.UpdateConfigPayload(command_id=uuid4().hex, config=dict(event.config))
        await self.send_command(event.device_id, protocol.T_UPDATE_CONFIG, payload)

    async def send_command(self, device_id: str, message_type: str, payload) -> None:
        envelope = Envelope(
            type=message_type,
            source="agent-gateway",
            payload=payload.model_dump(mode="json"),
        )
        await self.bus.publish(protocol.TOPIC_CMD.render(device_id=str(device_id)), envelope)

    # --- periodic ------------------------------------------------------
    async def sweep_presence(self) -> None:
        """Recompute fleet statuses; call on a timer. Emits DeviceWentOffline."""
        for t in fleet.sweep():
            await event_bus.publish(
                DeviceWentOffline(device_id=t.device_id, last_seen_at=None)
            )


__all__ = ["AgentGateway"]

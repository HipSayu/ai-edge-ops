"""FleetGateway — the server end of the edge protocol.

Binds a :class:`dqh.svc_core.messaging.MessageBus` to the existing application
services. Transport choice (in-memory / MQTT / ...) is the caller's; the gateway
only speaks the port.
"""

from __future__ import annotations

import logging

from dqh.svc_core.messaging import Envelope, MessageBus, MessageRouter, Subscription
from dqh.svc_core.presence import PresenceEvent, PresenceRegistry

from app.core import database
from app.core.config import settings
from app.core.events import event_bus
from app.edge import protocol
from app.modules.deployment.domain import DeploymentActivated
from app.modules.fleet.schemas import HeartbeatIn
from app.modules.fleet.service import FleetService
from app.modules.model_registry.service import ModelRegistryService
from app.modules.observability.schemas import ViolationCreate
from app.modules.observability.service import ViolationService

logger = logging.getLogger("app.edge.gateway")


def _device_id(env: Envelope) -> int:
    """Devices set ``Envelope.source`` to their numeric id."""
    try:
        return int(env.source)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"bad device source {env.source!r}") from exc


class FleetGateway:
    def __init__(self, bus: MessageBus, *, session_factory=None) -> None:
        self.bus = bus
        self._session_factory = session_factory
        self.router = MessageRouter()
        self.presence = PresenceRegistry(
            stale_after=settings.offline_threshold_seconds / 2,
            offline_after=settings.offline_threshold_seconds,
        )
        self._subs: list[Subscription] = []

    def _session(self):
        """Resolve the session factory at call time (tests swap the module global)."""
        return (self._session_factory or database.async_session)()

    async def start(self) -> None:
        self.router.on(protocol.T_HEARTBEAT, self._on_heartbeat)
        self.router.on(protocol.T_VIOLATION, self._on_violation)
        self.router.on(protocol.T_STATE_REPORT, self._on_state_report)
        for pattern in (protocol.SUB_STATE, protocol.SUB_TELEMETRY, protocol.SUB_EVENTS):
            self._subs.append(await self.bus.subscribe(pattern, self.router.dispatch))
        event_bus.subscribe(DeploymentActivated, self._on_deployment_activated)
        logger.info("fleet gateway started (bus=%s)", type(self.bus).__name__)

    async def stop(self) -> None:
        for sub in self._subs:
            await sub.unsubscribe()
        self._subs.clear()

    # --- inbound (edge -> server) ---------------------------------------
    async def _on_heartbeat(self, env: Envelope) -> None:
        device_id = _device_id(env)
        p = protocol.HeartbeatPayload.model_validate(env.payload)
        async with self._session() as session:
            await FleetService(session).record_heartbeat(
                device_id,
                HeartbeatIn(
                    recorded_at=p.recorded_at,
                    cpu_percent=p.cpu_percent,
                    gpu_percent=p.gpu_percent,
                    mem_percent=p.mem_percent,
                    temperature_c=p.temperature_c,
                    fps=p.fps,
                    inference_latency_ms=p.inference_latency_ms,
                ),
            )
        self.presence.mark_seen(str(device_id))

    async def _on_violation(self, env: Envelope) -> None:
        device_id = _device_id(env)
        p = protocol.ViolationPayload.model_validate(env.payload)
        async with self._session() as session:
            await ViolationService(session).record(
                ViolationCreate(
                    device_id=device_id,
                    zone=p.zone,
                    violation_type=p.violation_type,
                    confidence=p.confidence,
                    image_path=p.image_path,
                    recorded_at=p.recorded_at,
                )
            )

    async def _on_state_report(self, env: Envelope) -> None:
        p = protocol.StateReportPayload.model_validate(env.payload)
        self.presence.mark_seen(env.source)
        logger.debug("state report from %s: %s", env.source, p.runtime_status)

    # --- outbound (server -> edge) -------------------------------------
    async def _on_deployment_activated(self, event: DeploymentActivated) -> None:
        async with self._session() as session:
            version = await ModelRegistryService(session).get_version(event.model_version_id)
            payload = protocol.DeployModelPayload(
                deployment_id=event.deployment_id,
                model_version_id=event.model_version_id,
                artifact_uri=version.artifact_uri,
                format=str(version.format),
            )
        await self.send_command(event.device_id, protocol.T_DEPLOY_MODEL, payload)

    async def send_command(self, device_id: int, message_type: str, payload) -> None:
        envelope = Envelope(
            type=message_type,
            source="fleet-gateway",
            payload=payload.model_dump(mode="json"),
        )
        await self.bus.publish(protocol.TOPIC_CMD.render(device_id=str(device_id)), envelope)

    # --- periodic ------------------------------------------------------
    def sweep_presence(self) -> list[PresenceEvent]:
        """Recompute presence; call on a timer. Returns status transitions."""
        return self.presence.evaluate()


__all__ = ["FleetGateway"]

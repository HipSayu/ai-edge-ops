"""Entrypoint: wires bus + link + agent + pipelines + local API, runs forever.

    python -m edge_agent.main       (or: edge-agent)
"""

from __future__ import annotations

import asyncio
import json
import logging

import edge_protocol as p
import uvicorn
from dqh.svc_core.config import MqttConfig
from dqh.svc_core.messaging import InMemoryMessageBus, MessageBus
from dqh.svc_core.transports.event_driven.mqtt import MqttMessageBus

from edge_agent.core.config import AgentSettings, load_settings
from edge_agent.core.hardware import detect_hardware
from edge_agent.core.identity import agent_version, primary_ip, uptime_s
from edge_agent.core.state import StateStore
from edge_agent.network.api import build_api
from edge_agent.network.link import EdgeLink, MqttLogHandler
from edge_agent.runtime import build_runtime
from edge_agent.services.agent import Agent
from edge_agent.services.backend import build_backend
from edge_agent.services.evidence import HttpEvidenceUploader
from edge_agent.services.telemetry import TelemetryPump
from edge_agent.utils.metrics import collect_metrics

logger = logging.getLogger("edge_agent")


def build_bus(settings: AgentSettings) -> MessageBus:
    if settings.transport == "memory":
        return InMemoryMessageBus()
    mqtt: MqttConfig = settings.mqtt.model_copy(
        update={
            "client_id": settings.mqtt.client_id or f"edge-{settings.device_id}",
            "will_topic": p.TOPIC_STATE.render(device_id=settings.device_id),
            "will_payload": json.dumps(
                {"type": p.T_STATE_REPORT, "source": settings.device_id,
                 "payload": {"runtime_status": "offline"}}
            ),
        }
    )
    return MqttMessageBus(mqtt)


async def run(settings: AgentSettings | None = None) -> None:
    settings = settings or load_settings()
    logging.basicConfig(level=settings.log_level)

    hw = detect_hardware(backend=settings.vision.backend, device=settings.vision.device)

    bus = build_bus(settings)
    runtime = build_runtime(
        "dummy" if settings.transport == "memory" else settings.vision.runtime,
        device=hw.device,
    )
    store = StateStore(settings.state_file)

    agent = Agent(settings, runtime=runtime, store=store)

    def heartbeat() -> p.HeartbeatPayload:
        """Health heartbeat = machine metrics + this agent's identity + active model."""
        hb = collect_metrics(hardware=hw)
        hb.active_model_version_id = store.state.reported.active_model_version_id
        if hb.capabilities is not None:
            hb.capabilities.agent_version = agent_version()
            hb.capabilities.ip_address = primary_ip()
            hb.capabilities.uptime_s = uptime_s()
        return hb

    link = EdgeLink(
        bus,
        device_id=settings.device_id,
        heartbeat_interval_s=settings.heartbeat_interval_s,
        on_command=agent.handle_command,
        heartbeat_extra=heartbeat,
    )
    agent.link = link
    evidence_uploader = HttpEvidenceUploader(
        settings.server.base_url,
        token=settings.server.enroll_token,
        timeout_s=settings.server.request_timeout_s,
    )

    backend = build_backend(
        hw.backend,
        settings,
        hw=hw,
        runtime=runtime,
        link=link,
        evidence_uploader=evidence_uploader,
    )

    telemetry = TelemetryPump(settings.telemetry, sink=link.send_telemetry, hardware=hw)

    await link.start()
    log_handler = MqttLogHandler(link)
    logging.getLogger("edge_agent").addHandler(log_handler)
    await backend.start()
    telemetry.start()

    async def reconcile_loop() -> None:
        while True:
            await asyncio.sleep(settings.reconcile_interval_s)
            await agent.reconcile()

    api_server = uvicorn.Server(
        uvicorn.Config(
            build_api(agent), host=settings.api_host, port=settings.api_port, log_level="warning"
        )
    )

    try:
        await asyncio.gather(api_server.serve(), reconcile_loop())
    finally:
        await telemetry.stop()
        await backend.stop()
        logging.getLogger("edge_agent").removeHandler(log_handler)
        await link.stop()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

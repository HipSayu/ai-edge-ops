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
from dqh.svc_core.messaging.transports.mqtt import MqttMessageBus

from edge_agent.agent import Agent
from edge_agent.api import build_api
from edge_agent.config import AgentSettings, load_settings
from edge_agent.link import EdgeLink
from edge_agent.pipeline import CameraPipeline
from edge_agent.runtime import build_runtime
from edge_agent.state import StateStore

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

    bus = build_bus(settings)
    runtime = build_runtime("dummy" if settings.transport == "memory" else "yolo")
    store = StateStore(settings.state_file)

    agent = Agent(settings, runtime=runtime, store=store)
    link = EdgeLink(
        bus,
        device_id=settings.device_id,
        heartbeat_interval_s=settings.heartbeat_interval_s,
        on_command=agent.handle_command,
    )
    agent.link = link

    pipelines = [
        CameraPipeline(
            cam, runtime=runtime, inference=settings.inference, on_violation=link.send_violation
        )
        for cam in settings.cameras
        if cam.enabled
    ]

    await link.start()
    for pl in pipelines:
        pl.start()

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
        for pl in pipelines:
            await pl.stop()
        await link.stop()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

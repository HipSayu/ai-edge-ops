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

from edge_agent.agent import Agent
from edge_agent.api import build_api
from edge_agent.config import AgentSettings, CameraConfig, load_settings
from edge_agent.evidence import HttpEvidenceUploader
from edge_agent.link import EdgeLink, MqttLogHandler
from edge_agent.pipeline import CameraPipeline
from edge_agent.runtime import build_runtime
from edge_agent.state import StateStore
from edge_agent.streaming import VideoPublisher, build_publisher

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
    evidence_uploader = HttpEvidenceUploader(
        settings.server.base_url,
        token=settings.server.enroll_token,
        timeout_s=settings.server.request_timeout_s,
    )

    pipelines = [
        CameraPipeline(
            cam,
            runtime=runtime,
            inference=settings.inference,
            on_violation=link.send_violation,
            device_id=settings.device_id,
            evidence_uploader=evidence_uploader,
            on_bbox_frame=link.send_bbox_frame,
        )
        for cam in settings.cameras
        if cam.enabled
    ]

    await link.start()
    log_handler = MqttLogHandler(link)
    logging.getLogger("edge_agent").addHandler(log_handler)
    for pl in pipelines:
        pl.start()

    publishers = await _start_camera_streams(settings, link)

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
        for pub in publishers:
            await pub.stop()
        for pl in pipelines:
            await pl.stop()
        logging.getLogger("edge_agent").removeHandler(log_handler)
        await link.stop()


async def _start_camera_streams(settings: AgentSettings, link: EdgeLink) -> list[VideoPublisher]:
    """Dial each enabled, mapped camera out to MediaMTX over WHIP.

    This is a raw ffmpeg process per camera reading straight from the device
    — independent of the inference pipeline's own frame loop. Best-effort: a
    camera that fails to start streaming doesn't stop inference/violation
    reporting for it. The publish token is requested over the existing MQTT
    link (see ``EdgeLink.request_stream_token``), not a new HTTP call — the
    edge device has no HTTP credential of its own, but the MQTT link is
    already authenticated (TLS client cert / username-password).
    """
    if not settings.streaming.enabled:
        return []
    publishers: list[VideoPublisher] = []
    for cam in settings.cameras:
        if not cam.enabled:
            continue
        if cam.camera_id is None:
            logger.warning("camera %s has no camera_id mapped; skipping stream", cam.id)
            continue
        try:
            await _start_one_stream(cam, settings, publishers, link)
        except Exception:  # noqa: BLE001 - one bad camera shouldn't block the rest
            logger.exception("could not start stream for camera %s", cam.id)
    return publishers


async def _start_one_stream(
    cam: CameraConfig,
    settings: AgentSettings,
    publishers: list[VideoPublisher],
    link: EdgeLink,
) -> None:
    token = await link.request_stream_token(cam.camera_id, timeout=settings.server.request_timeout_s)
    publisher = build_publisher(
        settings.streaming.kind,
        encoder=settings.streaming.encoder,
        bitrate_kbps=settings.streaming.bitrate_kbps,
    )
    await publisher.start(
        source=cam.source, whip_url=token.url, token=token.token, loop=cam.loop
    )
    publishers.append(publisher)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

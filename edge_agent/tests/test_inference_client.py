"""InferenceClient bridges the vision-runtime channel to the MQTT link."""

from __future__ import annotations

import asyncio
import datetime as dt

import edge_protocol as p
import pytest
from dqh.svc_core.contracts.messaging import Envelope
from edge_protocol.channel import channel_pair

from edge_agent.core.config import AgentSettings
from edge_agent.inference_client.client import InferenceClient


class _FakeLink:
    def __init__(self) -> None:
        self.bbox: list = []
        self.violations: list = []

    async def send_bbox_frame(self, payload) -> None:
        self.bbox.append(payload)

    async def send_violation(self, payload) -> None:
        self.violations.append(payload)

    async def request_stream_token(self, camera_id: int):
        return p.StreamTokenReplyPayload(
            url="http://mtx/cam_1/whip",
            path="cam_1",
            token="tok",
            expires_at=dt.datetime.now(dt.timezone.utc),
        )


@pytest.fixture
async def wired():
    runtime_ch, agent_ch = channel_pair()
    link = _FakeLink()
    client = InferenceClient(AgentSettings(transport="memory"), link)
    # inject the "connected" channel directly instead of a real unix socket
    client._channel = agent_ch
    client.connected = True
    task = asyncio.create_task(_pump(client, agent_ch))
    yield runtime_ch, link, client
    task.cancel()


async def _pump(client, channel):
    async for env in channel.messages():
        await client._on_message(env)


async def test_forwards_bbox_and_violation(wired):
    runtime_ch, link, _client = wired
    await runtime_ch.send(
        Envelope(
            type=p.T_BBOX_FRAME,
            source="cam-1",
            payload=p.BboxFramePayload(
                camera_id="cam-1", frame_ts=1.0, seq=1
            ).model_dump(mode="json"),
        )
    )
    await runtime_ch.send(
        Envelope(
            type=p.T_VIOLATION,
            source="cam-1",
            payload=p.ViolationPayload(
                zone="z", violation_type="no_helmet", confidence=0.9
            ).model_dump(mode="json"),
        )
    )
    await asyncio.sleep(0.05)
    assert len(link.bbox) == 1 and link.bbox[0].camera_id == "cam-1"
    assert len(link.violations) == 1 and link.violations[0].violation_type == "no_helmet"


async def test_answers_stream_token_request(wired):
    runtime_ch, _link, _client = wired
    await runtime_ch.send(
        Envelope(
            type=p.T_STREAM_TOKEN_REQUEST,
            source="vision-runtime",
            payload=p.StreamTokenRequestPayload(camera_id=1).model_dump(mode="json"),
        )
    )
    reply = None
    async for env in runtime_ch.messages():
        if env.type == p.T_VR_STREAM_TOKEN:
            reply = env
            break
    assert reply is not None
    assert p.StreamTokenReplyPayload.model_validate(reply.payload).token == "tok"

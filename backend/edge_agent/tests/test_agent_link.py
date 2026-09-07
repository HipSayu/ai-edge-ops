from __future__ import annotations

import asyncio

import edge_protocol as p
import pytest
from dqh.svc_core.messaging import Envelope, InMemoryMessageBus

from edge_agent.agent import Agent
from edge_agent.config import AgentSettings, InferenceConfig
from edge_agent.link import EdgeLink
from edge_agent.runtime.dummy import DummyRuntime
from edge_agent.state import StateStore


@pytest.fixture
async def wired(tmp_path, monkeypatch):
    async def _fake_fetch(uri, *, dest_dir, filename, **kw):
        path = tmp_path / filename
        path.write_bytes(b"weights")
        return str(path)

    monkeypatch.setattr("edge_agent.agent.fetch_artifact", _fake_fetch)

    settings = AgentSettings(
        device_id="dev-1",
        transport="memory",
        heartbeat_interval_s=999,
        state_file=str(tmp_path / "state.json"),
        inference=InferenceConfig(weights_dir=str(tmp_path)),
    )
    bus = InMemoryMessageBus()
    await bus.connect()
    runtime = DummyRuntime()
    agent = Agent(settings, runtime=runtime, store=StateStore(settings.state_file))
    link = EdgeLink(
        bus, device_id="dev-1", heartbeat_interval_s=999, on_command=agent.handle_command
    )
    agent.link = link

    inbox: dict[str, list[Envelope]] = {"ack": [], "state": []}
    await bus.subscribe(
        p.TOPIC_ACK.render(device_id="dev-1"), lambda e: inbox["ack"].append(e) or asyncio.sleep(0)
    )
    await bus.subscribe(
        p.TOPIC_STATE.render(device_id="dev-1"),
        lambda e: inbox["state"].append(e) or asyncio.sleep(0),
    )
    await link.start()
    yield agent, bus, inbox
    await link.stop()


async def test_heartbeat_is_published_on_start(wired):
    _agent, _bus, inbox = wired
    await asyncio.sleep(0.05)
    assert any(e.type == p.T_HEARTBEAT for e in inbox["state"])


async def test_deploy_command_loads_runtime_and_acks(wired):
    agent, bus, inbox = wired

    await bus.publish(
        p.TOPIC_CMD.render(device_id="dev-1"),
        Envelope(
            type=p.T_DEPLOY_MODEL,
            source="agent-gateway",
            payload=p.DeployModelPayload(
                command_id="c1",
                deployment_id=7,
                model_version_id=42,
                artifact_uri="https://example.com/mv-42.engine",
                format="engine",
            ).model_dump(mode="json"),
        ),
    )
    await asyncio.sleep(0.05)

    assert agent.runtime.loaded
    assert agent.runtime.model_version_id == 42
    assert agent.store.state.reported.runtime_status == "active"

    acks = [p.CommandAckPayload.model_validate(e.payload) for e in inbox["ack"]]
    assert acks and acks[-1].status == "succeeded" and acks[-1].deployment_id == 7


async def test_unknown_command_acks_failed(wired):
    agent, bus, inbox = wired
    await bus.publish(
        p.TOPIC_CMD.render(device_id="dev-1"),
        Envelope(type="command.bogus", source="x", payload={}),
    )
    await asyncio.sleep(0.05)
    acks = [p.CommandAckPayload.model_validate(e.payload) for e in inbox["ack"]]
    assert acks and acks[-1].status == "failed"

from __future__ import annotations

import asyncio

import edge_protocol as p
import pytest
from dqh.svc_core.messaging import Envelope, InMemoryMessageBus

from edge_agent.core.config import AgentSettings
from edge_agent.core.state import StateStore
from edge_agent.network.link import EdgeLink
from edge_agent.runner import DeployResult
from edge_agent.services.agent import Agent


class _Deployer:
    async def deploy(self, image: str) -> DeployResult:
        return DeployResult(True)

    async def restart(self) -> DeployResult:
        return DeployResult(True)

    def current_image(self) -> str | None:
        return None


@pytest.fixture
async def wired(tmp_path):
    settings = AgentSettings(
        device_id="dev-1",
        transport="memory",
        heartbeat_interval_s=999,
        state_file=str(tmp_path / "state.json"),
    )
    bus = InMemoryMessageBus()
    await bus.connect()
    agent = Agent(settings, store=StateStore(settings.state_file), deployer=_Deployer())
    link = EdgeLink(
        bus, device_id="dev-1", heartbeat_interval_s=999, on_command=agent.handle_command
    )
    agent.link = link

    inbox: dict[str, list[Envelope]] = {"ack": [], "state": []}

    async def _ack(e: Envelope) -> None:
        inbox["ack"].append(e)

    async def _state(e: Envelope) -> None:
        inbox["state"].append(e)

    await bus.subscribe(p.TOPIC_ACK.render(device_id="dev-1"), _ack)
    await bus.subscribe(p.TOPIC_STATE.render(device_id="dev-1"), _state)
    await link.start()
    yield agent, bus, inbox
    await link.stop()


async def test_heartbeat_is_published_on_start(wired):
    _agent, _bus, inbox = wired
    await asyncio.sleep(0.05)
    assert any(e.type == p.T_HEARTBEAT for e in inbox["state"])


async def test_deploy_without_image_acks_failed(wired):
    _agent, bus, inbox = wired
    await bus.publish(
        p.TOPIC_CMD.render(device_id="dev-1"),
        Envelope(
            type=p.T_DEPLOY_MODEL,
            source="agent-gateway",
            payload=p.DeployModelPayload(
                command_id="c1", deployment_id=7, image=""
            ).model_dump(mode="json"),
        ),
    )
    await asyncio.sleep(0.05)
    acks = [p.CommandAckPayload.model_validate(e.payload) for e in inbox["ack"]]
    assert acks and acks[-1].status == "failed"


async def test_unknown_command_acks_failed(wired):
    _agent, bus, inbox = wired
    await bus.publish(
        p.TOPIC_CMD.render(device_id="dev-1"),
        Envelope(type="command.bogus", source="x", payload={}),
    )
    await asyncio.sleep(0.05)
    acks = [p.CommandAckPayload.model_validate(e.payload) for e in inbox["ack"]]
    assert acks and acks[-1].status == "failed"

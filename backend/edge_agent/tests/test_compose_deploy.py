"""Image-based deploy: Agent._deploy through a fake ModelDeployer, and the
ComposeRunner env-file / rollback bookkeeping."""

from __future__ import annotations

import asyncio

import edge_protocol as p
import pytest
from dqh.svc_core.messaging import Envelope, InMemoryMessageBus

from edge_agent.core.config import AgentSettings, ComposeConfig
from edge_agent.core.state import StateStore
from edge_agent.network.link import EdgeLink
from edge_agent.runner import ComposeRunner, DeployResult
from edge_agent.services.agent import Agent


class FakeDeployer:
    def __init__(self, *, ok: bool = True) -> None:
        self.ok = ok
        self.deployed: list[str] = []
        self.restarts = 0
        self._image: str | None = None

    async def deploy(self, image: str) -> DeployResult:
        self.deployed.append(image)
        if self.ok:
            self._image = image
            return DeployResult(True)
        return DeployResult(False, "boom")

    async def restart(self) -> DeployResult:
        self.restarts += 1
        return DeployResult(True)

    def current_image(self) -> str | None:
        return self._image


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
    deployer = FakeDeployer()
    agent = Agent(
        settings,
        store=StateStore(settings.state_file),
        deployer=deployer,
    )
    link = EdgeLink(
        bus, device_id="dev-1", heartbeat_interval_s=999, on_command=agent.handle_command
    )
    agent.link = link
    acks: list[Envelope] = []

    async def _collect(e: Envelope) -> None:
        acks.append(e)

    await bus.subscribe(p.TOPIC_ACK.render(device_id="dev-1"), _collect)
    await link.start()
    yield agent, bus, deployer, acks
    await link.stop()


async def _send_deploy(bus, **kw):
    payload = p.DeployModelPayload(
        command_id="c1", deployment_id=7, model_version_id=42, **kw
    ).model_dump(mode="json")
    await bus.publish(
        p.TOPIC_CMD.render(device_id="dev-1"),
        Envelope(type=p.T_DEPLOY_MODEL, source="agent-gateway", payload=payload),
    )
    await asyncio.sleep(0.05)


async def test_image_deploy_pulls_and_reports_active(wired):
    agent, bus, deployer, acks = wired
    await _send_deploy(bus, image="reg/models/ppe@sha256:abc")

    assert deployer.deployed == ["reg/models/ppe@sha256:abc"]
    assert agent.store.state.reported.runtime_status == "active"
    assert agent.store.state.reported.active_model_version_id == 42
    assert agent.store.state.desired.image == "reg/models/ppe@sha256:abc"
    assert p.CommandAckPayload.model_validate(acks[-1].payload).status == "succeeded"


async def test_image_deploy_failure_reports_failed(wired):
    agent, bus, _deployer, acks = wired
    agent.deployer = FakeDeployer(ok=False)
    await _send_deploy(bus, image="reg/models/ppe@sha256:bad")

    assert agent.store.state.reported.runtime_status == "failed"
    assert "boom" in (agent.store.state.reported.detail or "")
    assert p.CommandAckPayload.model_validate(acks[-1].payload).status == "failed"


async def test_restart_command_calls_deployer(wired):
    _agent, bus, deployer, acks = wired
    await bus.publish(
        p.TOPIC_CMD.render(device_id="dev-1"),
        Envelope(type=p.T_RESTART, source="x", payload={}),
    )
    await asyncio.sleep(0.05)
    assert deployer.restarts == 1
    assert p.CommandAckPayload.model_validate(acks[-1].payload).status == "succeeded"


# --- ComposeRunner env bookkeeping (no docker needed) ------------------
async def test_compose_runner_env_roundtrip_and_rollback(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("INFERENCE_IMAGE=reg/models/ppe@sha256:old\nOTHER=x\n")
    runner = ComposeRunner(ComposeConfig(project_dir=str(tmp_path), env_file=str(env)))

    assert runner.current_image() == "reg/models/ppe@sha256:old"

    calls: list[tuple[str, ...]] = []

    async def fake_compose(*args: str) -> tuple[int, str]:
        calls.append(args)
        return (1, "pull error") if args[0] == "pull" else (0, "")

    monkeypatch.setattr(runner, "_compose", fake_compose)
    monkeypatch.setattr(runner, "_prune", lambda **kw: asyncio.sleep(0))

    result = await runner.deploy("reg/models/ppe@sha256:new")
    assert result.ok is False
    # rolled back to the previous image
    assert runner.current_image() == "reg/models/ppe@sha256:old"
    assert "OTHER=x" in env.read_text()

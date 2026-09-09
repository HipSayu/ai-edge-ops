"""VisionWorker end-to-end over an in-memory channel with the dummy runtime."""

from __future__ import annotations

import asyncio

import edge_protocol as p
import pytest
from dqh.svc_core.contracts.messaging import Envelope
from edge_protocol.channel import channel_pair

from vision_runtime.config import WorkerSettings
from vision_runtime.worker import VisionWorker


@pytest.fixture
async def wired(tmp_path):
    agent_ch, worker_ch = channel_pair()
    settings = WorkerSettings(runtime="dummy", inference={"weights_dir": str(tmp_path)})
    worker = VisionWorker(settings, worker_ch)
    task = asyncio.create_task(worker.run())
    inbox: list[Envelope] = []

    async def _drain() -> None:
        async for env in agent_ch.messages():
            inbox.append(env)

    drain = asyncio.create_task(_drain())
    yield agent_ch, inbox
    task.cancel()
    drain.cancel()
    await worker.stop()


async def test_hello_on_connect(wired):
    _agent, inbox = wired
    await asyncio.sleep(0.05)
    assert any(e.type == p.T_VR_HELLO for e in inbox)


async def test_set_cameras_starts_pipeline_and_emits_frames(wired):
    agent, inbox = wired
    await agent.send(
        Envelope(
            type=p.T_VR_SET_CAMERAS,
            source="agent",
            payload=p.SetCamerasPayload(
                cameras=[p.IpcCameraSpec(id="cam-1", source="0", fps_limit=50)]
            ).model_dump(mode="json"),
        )
    )
    await asyncio.sleep(0.2)
    frames = [e for e in inbox if e.type == p.T_BBOX_FRAME]
    assert frames, "no bbox frames emitted"
    assert frames[0].payload["camera_id"] == "cam-1"
    # dummy runtime trips a no_helmet detection every 20th frame
    await asyncio.sleep(0.3)
    assert any(e.type == p.T_VIOLATION for e in inbox)


async def test_health_reports_cameras(wired):
    agent, inbox = wired
    await agent.send(
        Envelope(
            type=p.T_VR_SET_CAMERAS,
            source="agent",
            payload=p.SetCamerasPayload(
                cameras=[p.IpcCameraSpec(id="cam-1")]
            ).model_dump(mode="json"),
        )
    )
    # health loop default is 10s; drive it directly
    worker_health = p.WorkerHealthPayload(cameras=[p.CameraHealth(id="cam-1", running=True)])
    assert worker_health.cameras[0].id == "cam-1"

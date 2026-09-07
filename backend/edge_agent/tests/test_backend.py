from __future__ import annotations

import edge_protocol as p
import pytest

from edge_agent.core.config import AgentSettings, CameraConfig, StreamingConfig
from edge_agent.core.hardware import Hardware
from edge_agent.runtime.dummy import DummyRuntime
from edge_agent.services.backend import ComposedBackend, build_backend

_HW = Hardware(
    arch="x86_64", is_jetson=False, has_cuda=False, has_mps=False, has_deepstream=False,
    encoders=frozenset(), backend="composed", device="cpu", model_formats=("onnx",),
)


class _FakeLink:
    def __init__(self):
        self.bbox: list = []
        self.violations: list = []
        self.stream_requests: list = []

    async def send_bbox_frame(self, payload):
        self.bbox.append(payload)

    async def send_violation(self, payload):
        self.violations.append(payload)

    async def request_stream_token(self, camera_id, *, timeout=10.0):
        self.stream_requests.append(camera_id)
        return p.StreamTokenReplyPayload(
            url="http://mediamtx/cam_1/whip", path="cam_1", token="t",
            expires_at=__import__("datetime").datetime(2030, 1, 1),
        )


def _settings(**kw) -> AgentSettings:
    return AgentSettings(device_id="dev-1", transport="memory", **kw)


async def test_build_backend_defaults_to_composed():
    backend = build_backend(
        "composed", _settings(), hw=_HW, runtime=DummyRuntime(), link=_FakeLink()
    )
    assert isinstance(backend, ComposedBackend)


async def test_composed_backend_starts_pipeline_without_streaming():
    link = _FakeLink()
    settings = _settings(cameras=[CameraConfig(id="cam-a", source="0")])
    backend = ComposedBackend(settings, hw=_HW, runtime=DummyRuntime(), link=link)
    await backend.start()
    try:
        assert len(backend._pipelines) == 1
        assert link.stream_requests == []  # streaming disabled by default
    finally:
        await backend.stop()
    assert backend._pipelines == []


async def test_composed_backend_requests_stream_token_when_enabled():
    link = _FakeLink()
    settings = _settings(
        cameras=[CameraConfig(id="cam-a", source="0", camera_id=1)],
        streaming=StreamingConfig(enabled=True, kind="null"),
    )
    backend = ComposedBackend(settings, hw=_HW, runtime=DummyRuntime(), link=link)
    await backend.start()
    try:
        assert link.stream_requests == [1]
        assert len(backend._publishers) == 1
    finally:
        await backend.stop()


async def test_deepstream_backend_unavailable_raises():
    with pytest.raises(RuntimeError, match="pyds"):
        build_backend(
            "deepstream", _settings(), hw=_HW, runtime=DummyRuntime(), link=_FakeLink()
        )

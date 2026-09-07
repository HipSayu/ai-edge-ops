from __future__ import annotations

import sys

from edge_agent.config import CameraConfig, InferenceConfig
from edge_agent.pipeline import CameraPipeline
from edge_agent.helpers.ppe import evaluate_ppe
from edge_agent.helpers.video import frames
from edge_agent.runtime.base import Detection


def _d(label: str) -> Detection:
    return Detection(label=label, confidence=0.9, bbox=(0, 0, 1, 1))


def test_no_person_no_violation():
    assert evaluate_ppe([_d("helmet"), _d("vest")], ["helmet", "vest"]) == []


def test_missing_ppe_is_violation():
    assert evaluate_ppe([_d("person"), _d("vest")], ["helmet", "vest"]) == ["no_helmet"]


def test_explicit_negative_class_passthrough():
    out = evaluate_ppe([_d("person"), _d("no_helmet")], ["helmet"])
    assert "no_helmet" in out


def test_fully_compliant():
    assert evaluate_ppe([_d("person"), _d("helmet"), _d("vest")], ["helmet", "vest"]) == []


def test_video_frames_can_loop_at_eof(monkeypatch):
    class FakeCapture:
        def __init__(self, source):
            self.source = source
            self.frames = [f"frame-{source}"]

        def read(self):
            if self.frames:
                return True, self.frames.pop()
            return False, None

        def release(self):
            pass

    opened = []

    class FakeCV2:
        def VideoCapture(self, source):
            opened.append(source)
            return FakeCapture(source)

    monkeypatch.setitem(sys.modules, "cv2", FakeCV2())

    source_frames = frames("clip.mp4", loop=True)
    assert next(source_frames) == "frame-clip.mp4"
    assert next(source_frames) == "frame-clip.mp4"
    assert opened == ["clip.mp4", "clip.mp4"]


async def test_violation_upload_path_is_attached():
    class Uploader:
        async def upload(self, frame, **kwargs):
            assert frame == "frame"
            assert kwargs["device_id"] == "edge-1"
            return "http://server/evidence/frame.jpg"

    events = []

    async def sink(payload):
        events.append(payload)

    pipeline = CameraPipeline(
        CameraConfig(id="cam-1"),
        runtime=None,
        inference=InferenceConfig(),
        on_violation=sink,
        device_id="edge-1",
        evidence_uploader=Uploader(),
    )
    await pipeline._emit("no_helmet", [_d("person"), _d("no_helmet")], "frame")

    assert events[0].image_path == "http://server/evidence/frame.jpg"

"""PPE rule + frame source."""

from __future__ import annotations

from vision_runtime.capture.frame_source import frames
from vision_runtime.rules.ppe import evaluate_ppe
from vision_runtime.runtime.base import Detection


def _d(label: str) -> Detection:
    return Detection(label=label, confidence=0.9, bbox=(0.1, 0.1, 0.2, 0.2))


def test_no_person_no_violation():
    assert evaluate_ppe([_d("helmet")], ["helmet", "vest"]) == []


def test_missing_required_gear():
    assert evaluate_ppe([_d("person"), _d("helmet")], ["helmet", "vest"]) == ["no_vest"]


def test_explicit_negative_class():
    out = evaluate_ppe([_d("person"), _d("no_helmet")], ["helmet"])
    assert out == ["no_helmet"]


def test_frame_source_loops_at_eof(monkeypatch):
    import sys

    reads = iter([(True, "f1"), (False, None), (True, "f2"), (False, None)])

    class _Cap:
        def __init__(self, source):
            pass

        def read(self):
            return next(reads, (False, None))

        def release(self):
            pass

    monkeypatch.setitem(sys.modules, "cv2", type("cv2", (), {"VideoCapture": _Cap}))

    gen = frames("clip.mp4", loop=True)
    assert next(gen) == "f1"
    assert next(gen) == "f2"


def test_frame_source_no_cv2_yields_placeholder(monkeypatch):
    import sys

    from vision_runtime.capture.frame_source import NO_CV2_FRAME

    monkeypatch.setitem(sys.modules, "cv2", None)  # force ModuleNotFoundError on import
    gen = frames("0")
    assert next(gen) is NO_CV2_FRAME

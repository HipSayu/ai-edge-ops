from __future__ import annotations

import edge_agent.core.hardware as hw_mod
from edge_agent.core.hardware import detect_hardware


def _stub(monkeypatch, *, cuda=False, mps=False, deepstream=False, jetson=False,
          arch="x86_64", encoders=frozenset()):
    monkeypatch.setattr(hw_mod, "_has_cuda", lambda: cuda)
    monkeypatch.setattr(hw_mod, "_has_mps", lambda: mps)
    monkeypatch.setattr(hw_mod, "_has_deepstream", lambda: deepstream)
    monkeypatch.setattr(hw_mod, "_is_jetson", lambda: jetson)
    monkeypatch.setattr(hw_mod, "_ffmpeg_encoders", lambda: encoders)
    monkeypatch.setattr(hw_mod.platform, "machine", lambda: arch)


def test_auto_plain_cpu_box(monkeypatch):
    _stub(monkeypatch)
    hw = detect_hardware()
    assert hw.backend == "composed"
    assert hw.device == "cpu"
    assert hw.model_formats == ("onnx",)


def test_auto_picks_cuda_and_deepstream(monkeypatch):
    _stub(monkeypatch, cuda=True, deepstream=True, jetson=True, arch="aarch64")
    hw = detect_hardware()
    assert hw.backend == "deepstream"
    assert hw.device == "cuda:0"
    assert "engine" in hw.model_formats


def test_auto_cuda_without_deepstream_stays_composed(monkeypatch):
    _stub(monkeypatch, cuda=True)
    hw = detect_hardware()
    assert hw.backend == "composed"
    assert hw.device == "cuda:0"
    assert hw.model_formats[0] == "engine"


def test_apple_silicon(monkeypatch):
    _stub(monkeypatch, mps=True, arch="arm64")
    hw = detect_hardware()
    assert hw.device == "mps"
    assert hw.backend == "composed"


def test_explicit_override_downgrades_with_warning(monkeypatch):
    _stub(monkeypatch)  # no cuda, no deepstream
    hw = detect_hardware(backend="deepstream", device="cuda:0")
    assert hw.backend == "composed"
    assert hw.device == "cpu"


def test_explicit_cpu_on_gpu_box_is_respected(monkeypatch):
    _stub(monkeypatch, cuda=True, deepstream=True)
    hw = detect_hardware(backend="composed", device="cpu")
    assert hw.backend == "composed"
    assert hw.device == "cpu"

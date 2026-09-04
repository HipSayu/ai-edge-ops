"""Inference runtime — pluggable. ``DummyRuntime`` needs no ML deps."""

from __future__ import annotations

from edge_agent.runtime.base import Detection, InferenceRuntime
from edge_agent.runtime.dummy import DummyRuntime


def build_runtime(kind: str = "dummy") -> InferenceRuntime:
    if kind == "yolo":
        from edge_agent.runtime.yolo import YoloRuntime

        return YoloRuntime()
    return DummyRuntime()


__all__ = ["Detection", "InferenceRuntime", "DummyRuntime", "build_runtime"]

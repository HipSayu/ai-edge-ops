"""Inference runtime — pluggable. ``DummyRuntime`` needs no ML deps."""

from __future__ import annotations

import logging

from vision_runtime.runtime.base import Detection, InferenceRuntime
from vision_runtime.runtime.dummy import DummyRuntime

logger = logging.getLogger("vision_runtime.runtime")


def build_runtime(kind: str = "auto", *, device: str = "cpu") -> InferenceRuntime:
    """``auto`` uses YOLO when the ``inference`` extra is installed, else Dummy.
    ``yolo`` / ``dummy`` force the choice (``yolo`` raises if unavailable).
    """
    if kind == "dummy":
        return DummyRuntime()
    try:
        from vision_runtime.runtime.yolo import YoloRuntime

        return YoloRuntime(device=device)
    except ModuleNotFoundError:
        if kind == "yolo":
            raise
        logger.warning("ultralytics not installed; falling back to DummyRuntime")
        return DummyRuntime()


__all__ = ["Detection", "InferenceRuntime", "DummyRuntime", "build_runtime"]

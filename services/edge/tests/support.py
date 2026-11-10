"""Test doubles shared by the edge tests: a frame, and a CameraLogic driven the way the stream drives it."""

from dataclasses import dataclass

import numpy as np

from edge.application.camera_logic import CameraLogic


@dataclass(frozen=True)
class Frame:
    image: np.ndarray
    ts_sec: float


class Pipe:
    """A CameraLogic fed by a fake detector: `process(frame)` is what the DeepStream probe does for one camera frame.
    Anything else (cooldown clock, sinks, zones) is the logic's own and is read and set through to it."""

    def __init__(self, logic: CameraLogic, detector) -> None:
        object.__setattr__(self, "logic", logic)
        object.__setattr__(self, "detector", detector)

    def process(self, frame: Frame) -> int:
        height, width = frame.image.shape[:2]
        return self.logic.handle(frame.ts_sec, width, height, self.detector.detect(frame.image), lambda: frame.image)

    def __getattr__(self, name):
        return getattr(self.logic, name)

    def __setattr__(self, name, value) -> None:
        if name == "detector":
            object.__setattr__(self, name, value)
        else:
            setattr(self.logic, name, value)

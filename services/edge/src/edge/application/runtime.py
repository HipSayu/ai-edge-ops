"""Runs the streams of this node: one DeepStream pipeline for all its cameras, and the logic of each camera."""

import logging
import threading
from dataclasses import dataclass, field

import numpy as np
from collections.abc import Callable

from edge.application.camera_logic import CameraLogic
from edge.application.ports import DetectionStream
from edge.domain.detection import Detection

log = logging.getLogger("edge.runtime")


@dataclass
class NodeStream:
    """One node: its stream, and the logic of each camera by the camera's id."""

    node_id: str
    stream: DetectionStream
    cameras: dict[int, CameraLogic]

    def handle(self, camera_id: int, ts_sec: float, width: int, height: int, detections: list[Detection],
               get_image: Callable[[], np.ndarray]) -> None:
        logic = self.cameras.get(camera_id)
        if logic is None:
            return
        try:
            logic.handle(ts_sec, width, height, detections, get_image)
        except Exception:  # one camera's logic that breaks must not stop the others sharing the stream
            log.exception("camera %s failed on a detection", camera_id)


class EdgeRuntime:
    def __init__(self, nodes: list[NodeStream]) -> None:
        self._nodes = nodes
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        for node in self._nodes:
            thread = threading.Thread(target=self._guard, args=(node,), name=f"stream-{node.node_id}", daemon=True)
            thread.start()
            self._threads.append(thread)

    def _guard(self, node: NodeStream) -> None:
        try:
            node.stream.run(node.handle, self._stop)
        except Exception:  # a node whose stream broke must not stop the other nodes of this process
            log.exception("the stream of node %s stopped", node.node_id)

    def wait(self) -> None:
        for t in self._threads:
            t.join()

    def stop(self) -> None:
        self._stop.set()
        for t in self._threads:
            t.join(timeout=10)

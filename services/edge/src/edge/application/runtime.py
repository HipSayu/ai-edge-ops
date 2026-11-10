"""Runs every camera of this node, one thread each."""

import logging
import threading

from edge.application.pipeline import CameraPipeline

log = logging.getLogger("edge.runtime")


class EdgeRuntime:
    def __init__(self, pipelines: list[CameraPipeline]) -> None:
        self._pipelines = pipelines
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        for p in self._pipelines:
            thread = threading.Thread(target=self._guard, args=(p,), name=f"camera-{p.camera_id}", daemon=True)
            thread.start()
            self._threads.append(thread)

    def _guard(self, pipeline: CameraPipeline) -> None:
        try:
            pipeline.run(self._stop)
        except Exception:  # one broken camera must not stop the others
            log.exception("camera %s stopped", pipeline.camera_id)

    def wait(self) -> None:
        for t in self._threads:
            t.join()

    def stop(self) -> None:
        self._stop.set()
        for t in self._threads:
            t.join(timeout=5)

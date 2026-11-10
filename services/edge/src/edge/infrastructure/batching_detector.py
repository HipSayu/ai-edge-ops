"""One model call for the frames of many cameras.

Every camera detects in its own thread and asks `detect(frame)`; this gathers the frames that are waiting at the same
moment and runs them through the model as one batch, then hands each camera its own answer. A GPU does a batch of eight
in not much more time than one frame, so the cameras sharing a model each get several times more detections a second.
A camera never waits for another one: only the frames already waiting go into a batch."""

import queue
import threading
from collections.abc import Callable
from concurrent.futures import Future
from typing import Protocol

import numpy as np

from edge.domain.detection import Detection


class BatchDetector(Protocol):
    def detect_batch(self, images: list[np.ndarray]) -> list[list[Detection]]: ...


class BatchingDetector:
    """The Detector port, over a model that can look at several frames in one call."""

    def __init__(self, inner: BatchDetector, max_batch: int = 8, gather_sec: float = 0.004) -> None:
        self._inner, self._max_batch, self._gather = inner, max_batch, gather_sec
        self._waiting: queue.Queue[tuple[np.ndarray, Future]] = queue.Queue()
        self.batches: list[int] = []  # the size of recent batches (kept short), to see how well they fill
        threading.Thread(target=self._run, name="batch-detector", daemon=True).start()

    def detect(self, image: np.ndarray) -> list[Detection]:
        done: Future = Future()
        self._waiting.put((image, done))
        return done.result()

    def _run(self) -> None:
        while True:
            batch = [self._waiting.get()]  # waits for the first frame
            try:
                while len(batch) < self._max_batch:  # then takes what is already there, or arrives within a moment
                    batch.append(self._waiting.get(timeout=self._gather))
            except queue.Empty:
                pass
            self.batches = (self.batches + [len(batch)])[-50:]
            try:
                results = self._inner.detect_batch([image for image, _ in batch])
            except Exception as error:  # every camera of the batch gets it, and the next batch goes on
                for _, done in batch:
                    done.set_exception(error)
                continue
            for (_, done), found in zip(batch, results):
                done.set_result(found)

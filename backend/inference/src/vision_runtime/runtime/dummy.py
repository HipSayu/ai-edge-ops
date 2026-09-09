"""Zero-dependency runtime — for CI, local dev, and demo without a GPU.

Emits a deterministic-ish stream: every Nth frame is a "no_helmet" detection.
"""

from __future__ import annotations

import itertools
from typing import Any

from vision_runtime.runtime.base import Detection, InferenceRuntime


class DummyRuntime(InferenceRuntime):
    def __init__(self, *, violate_every: int = 20) -> None:
        self._loaded = False
        self._mv_id: int | None = None
        self._counter = itertools.count()
        self._violate_every = violate_every

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def model_version_id(self) -> int | None:
        return self._mv_id

    async def load(self, *, weights_path: str, model_version_id: int, config: dict) -> None:
        self._mv_id = model_version_id
        self._loaded = True

    async def infer(self, frame: Any) -> list[Detection]:
        n = next(self._counter)
        if self._violate_every and n % self._violate_every == 0:
            return [Detection(label="no_helmet", confidence=0.88, bbox=(0.4, 0.3, 0.6, 0.7))]
        return [Detection(label="person", confidence=0.95, bbox=(0.35, 0.25, 0.65, 0.9))]

    async def unload(self) -> None:
        self._loaded = False
        self._mv_id = None

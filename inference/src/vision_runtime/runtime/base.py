from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2 (normalised)


class InferenceRuntime(ABC):
    """Loads a model artifact and runs detection on frames."""

    @property
    @abstractmethod
    def loaded(self) -> bool: ...

    @property
    @abstractmethod
    def model_version_id(self) -> int | None: ...

    @abstractmethod
    async def load(self, *, weights_path: str, model_version_id: int, config: dict) -> None: ...

    @abstractmethod
    async def infer(self, frame: Any) -> list[Detection]: ...

    @abstractmethod
    async def unload(self) -> None: ...

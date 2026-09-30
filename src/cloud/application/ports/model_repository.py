from pathlib import Path
from typing import Protocol

from src.cloud.domain.value_objects.model_location import ModelLocation
from src.cloud.domain.value_objects.model_ref import ModelRef


class ModelRepository(Protocol):
    """Where model artifacts (.pt / .onnx) live; edge nodes download from the resolved location."""

    async def resolve(self, ref: ModelRef) -> ModelLocation:
        """Pin `ref.revision` to a commit sha so every node gets the same file."""
        ...

    async def upload(self, local_path: Path, ref: ModelRef) -> ModelLocation: ...

    async def ping(self) -> bool: ...

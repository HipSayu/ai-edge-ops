from typing import Protocol


class ArtifactFetcher(Protocol):
    async def fetch(self, uri: str) -> str:
        """Materialize a model/artifact locally; returns the host path to mount into the runtime."""
        ...

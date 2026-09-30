from typing import Protocol


class Embedder(Protocol):
    """Text -> dense vectors. Documents and queries may be embedded differently by some providers."""

    @property
    def dimensions(self) -> int: ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...

from typing import Protocol

from src.assistant.domain.knowledge.document import Document, DocumentKind
from src.assistant.domain.knowledge.vector_hit import VectorHit


class VectorStore(Protocol):
    """Embeddings only: a vector per document id (plus its kind, to filter, and content hash, to skip unchanged
    documents). Document content never goes here; it is read from the DocumentRepository."""

    async def ensure_collection(self, dimensions: int) -> None: ...

    async def upsert(self, document: Document, vector: list[float]) -> None: ...

    async def search(self, vector: list[float], limit: int, kinds: list[DocumentKind] | None = None) -> list[VectorHit]: ...

    async def document_hash(self, document_id: str) -> str | None:
        """Content hash stored at last ingest, to skip unchanged documents."""
        ...

    async def document_ids(self) -> set[str]: ...

    async def delete(self, document_ids: list[str]) -> None: ...

    async def ping(self) -> bool: ...

    async def close(self) -> None: ...

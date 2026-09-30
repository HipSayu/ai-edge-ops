import logging

from src.assistant.application.ports.embedder import Embedder
from src.assistant.domain.knowledge.document import DocumentKind
from src.assistant.domain.knowledge.search_result import SearchResult
from src.assistant.application.ports.document_repository import DocumentRepository
from src.assistant.application.ports.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RetrievalService:
    """Vector search for ids, then the documents themselves from the local knowledge base."""

    def __init__(
        self, embedder: Embedder, store: VectorStore, documents: DocumentRepository,
        top_k: int = 5, min_score: float = 0.0,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._documents = documents
        self._top_k = top_k
        self._min_score = min_score

    async def search(
        self, query: str, kinds: list[DocumentKind] | None = None, limit: int | None = None
    ) -> list[SearchResult]:
        vector = await self._embedder.embed_query(query)
        results = []
        for hit in await self._store.search(vector, limit or self._top_k, kinds):
            document = self._documents.get(hit.document_id)
            if document is None:  # indexed but gone from disk: stale until the next ingest
                logger.warning("vector for missing document=%s", hit.document_id)
            elif hit.score >= self._min_score:
                results.append(SearchResult(document, hit.score))
        return results

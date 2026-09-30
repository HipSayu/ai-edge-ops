import logging
from dataclasses import dataclass, field

from src.assistant.application.ports.embedder import Embedder
from src.assistant.domain.knowledge.document import Document
from src.assistant.application.ports.document_repository import DocumentRepository
from src.assistant.application.ports.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class IngestionReport:
    ingested: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


class IngestionService:
    """Syncs the vector store with the local knowledge base: embeds each document's title + summary and stores
    only the vector under the document id. Not chunked: search matches summaries, the full text is read locally.

    Idempotent: unchanged documents (same content hash) are skipped, documents without a summary too, and vectors
    of documents no longer on disk are removed.
    """

    def __init__(self, documents: DocumentRepository, embedder: Embedder, store: VectorStore) -> None:
        self._documents = documents
        self._embedder = embedder
        self._store = store

    async def sync(self, force: bool = False) -> IngestionReport:
        await self._store.ensure_collection(self._embedder.dimensions)
        report = IngestionReport()
        local: set[str] = set()
        for document in self._documents.all():
            if not document.summary:
                logger.warning("skipped %s: no front matter summary to search by", document.id)
                report.skipped.append(document.id)
                continue
            local.add(document.id)
            (report.ingested if await self.ingest(document, force) else report.unchanged).append(document.id)
        report.removed = sorted(await self._store.document_ids() - local)
        await self._store.delete(report.removed)
        return report

    async def ingest(self, document: Document, force: bool = False) -> bool:
        """Returns False when the stored vector is already up to date."""
        if not force and await self._store.document_hash(document.id) == document.content_hash:
            return False
        [vector] = await self._embedder.embed_documents([f"{document.title}\n\n{document.summary}"])
        await self._store.upsert(document, vector)
        logger.info("ingested document=%s", document.id)
        return True

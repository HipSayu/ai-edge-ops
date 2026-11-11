"""The KnowledgeBase port over a folder of markdown files, searched by meaning.

The folder stays the source of truth. Every search first brings the vector store up to date (new, changed and removed
files), so documents are found without a restart."""

from pathlib import Path

from cloud.application.ports import Embedder, VectorStore
from cloud.domain.policy.regulation import Passage
from cloud.infrastructure.knowledge.documents import Document, load_documents


class DocumentKnowledgeBase:
    def __init__(self, store: VectorStore, embedder: Embedder, folder: Path, min_score: float = 0.0) -> None:
        self._store = store
        self._embedder = embedder
        self._folder = folder
        self._min_score = min_score

    def has_documents(self) -> bool:
        return bool(load_documents(self._folder))

    def search(self, query: str, top_k: int = 3) -> list[Passage]:
        self._sync(load_documents(self._folder))
        return self._store.search(self._embedder.embed_query(query), top_k, self._min_score)

    def _sync(self, documents: list[Document]) -> None:
        indexed = self._store.digests()
        current = {d.name for d in documents}
        for name in indexed.keys() - current:
            self._store.remove(name)
        for document in documents:
            if indexed.get(document.name) != self._stamp(document) and self._index(document):
                return self._sync(documents)  # the vector size changed: the other files went with the old collection

    def _stamp(self, document: Document) -> str:
        """What the store keeps per file: the content and the model that embedded it, so either change re-indexes it."""
        return f"{self._embedder.name}:{document.digest}"

    def _index(self, document: Document) -> bool:
        vectors = self._embedder.embed_documents([f"{p.heading}\n{p.text}" for p in document.passages])
        return self._store.replace(document.name, self._stamp(document), document.passages, vectors)

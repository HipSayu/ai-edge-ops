import logging
from pathlib import Path

from src.assistant.domain.knowledge.document import Document, DocumentKind
from src.assistant.application.ports.document_loader import DocumentLoader

logger = logging.getLogger(__name__)


class LocalDocumentRepository:
    """Knowledge files on local disk, laid out as `<root>/<kind>/**` (e.g. docs/knowledge/runbook/disk_full.md).

    Folders that are not a DocumentKind (eval/, templates) are ignored. Files are read once, on first use;
    document ids are `<kind>/<path under the kind folder>`, the same ids the vector store keeps.
    """

    def __init__(self, root: Path, loaders: list[DocumentLoader]) -> None:
        self._root = root
        self._loaders = loaders
        self._documents: dict[str, Document] | None = None

    def all(self) -> list[Document]:
        return list(self._load().values())

    def get(self, document_id: str) -> Document | None:
        return self._load().get(document_id)

    def _load(self) -> dict[str, Document]:
        if self._documents is None:
            self._documents = {}
            for kind in DocumentKind:
                folder = self._root / kind.value
                for file in sorted(folder.rglob("*")) if folder.is_dir() else []:
                    loader = next((l for l in self._loaders if l.supports(file)), None) if file.is_file() else None
                    if loader is not None:
                        document = loader.load(file, folder, kind)
                        self._documents[document.id] = document
            logger.info("knowledge base: %d documents under %s", len(self._documents), self._root)
        return self._documents

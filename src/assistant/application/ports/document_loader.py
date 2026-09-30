from pathlib import Path
from typing import Protocol

from src.assistant.domain.knowledge.document import Document, DocumentKind


class DocumentLoader(Protocol):
    def supports(self, path: Path) -> bool: ...

    def load(self, path: Path, root: Path, kind: DocumentKind) -> Document: ...

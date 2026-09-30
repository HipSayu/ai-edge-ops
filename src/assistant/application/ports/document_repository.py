from typing import Protocol

from src.assistant.domain.knowledge.document import Document


class DocumentRepository(Protocol):
    """Where knowledge content lives (title, summary, full text, tools); looked up by document id."""

    def all(self) -> list[Document]: ...

    def get(self, document_id: str) -> Document | None: ...

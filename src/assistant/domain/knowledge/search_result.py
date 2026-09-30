from dataclasses import dataclass

from src.assistant.domain.knowledge.document import Document


@dataclass(frozen=True)
class SearchResult:
    """A matched document, read from the local knowledge base, with its similarity score."""

    document: Document
    score: float

    @property
    def citation(self) -> str:
        return self.document.source

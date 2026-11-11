from dataclasses import dataclass


@dataclass(frozen=True)
class Passage:
    """A section of a regulation document, with the score it got for a query."""

    source: str  # file name
    heading: str
    text: str
    score: float = 0.0

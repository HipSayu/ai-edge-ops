from dataclasses import dataclass


@dataclass(frozen=True)
class VectorHit:
    """What the vector store returns: only which document matched and how well; content lives locally."""

    document_id: str
    score: float

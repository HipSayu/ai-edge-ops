"""Reads the regulation files the customer put in volume/regulations/*.md: one passage per markdown section."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from cloud.domain.policy.regulation import Passage


@dataclass(frozen=True)
class Document:
    name: str
    digest: str  # changes whenever the file content changes
    passages: list[Passage]


def _split(name: str, stem: str, text: str) -> list[Passage]:
    """One passage per markdown section (heading + the lines under it)."""
    passages, heading, lines = [], stem, []

    def flush() -> None:
        body = "\n".join(lines).strip()
        if body:
            passages.append(Passage(name, heading, body))

    for line in text.splitlines():
        if line.startswith("#"):
            flush()
            heading, lines = line.lstrip("# ").strip() or stem, []
        else:
            lines.append(line)
    flush()
    return passages


def load_documents(folder: Path) -> list[Document]:
    files = [f for f in sorted(folder.glob("*.md")) if f.name.lower() != "readme.md"]
    documents = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        passages = _split(f.name, f.stem, text)
        if passages:
            documents.append(Document(f.name, hashlib.sha256(text.encode("utf-8")).hexdigest(), passages))
    return documents

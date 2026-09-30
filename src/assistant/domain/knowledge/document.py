import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DocumentKind(StrEnum):
    DOC = "doc"
    GUIDE = "guide"
    SKILL = "skill"
    RUNBOOK = "runbook"


@dataclass(frozen=True)
class Document:
    """One source file of knowledge; `id` is stable across re-ingests (e.g. the relative path).

    `metadata` is the file's front matter; its `summary` is what search matches the document by.
    """

    id: str
    source: str
    title: str
    kind: DocumentKind
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def summary(self) -> str:
        value = self.metadata.get("summary") or ""
        return " ".join(str(v) for v in value) if isinstance(value, list) else str(value).strip()

    @property
    def tools(self) -> tuple[str, ...]:
        return tuple(str(t) for t in self.metadata.get("tools") or ())

    @property
    def content_hash(self) -> str:
        # Front matter counts: editing only the summary must re-ingest the document
        meta = json.dumps(self.metadata, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(f"{meta}\n{self.text}".encode("utf-8")).hexdigest()

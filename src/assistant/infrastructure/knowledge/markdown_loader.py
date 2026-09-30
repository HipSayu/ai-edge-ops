import re
from pathlib import Path

import yaml

from src.assistant.domain.knowledge.document import Document, DocumentKind

_TITLE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_FRONT_MATTER = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)


class MarkdownLoader:
    """`.md` files with optional YAML front matter, kept as metadata rather than text.

    Title: front matter `name`, else the first H1, else the file name.
    """

    SUFFIXES = (".md", ".markdown")

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUFFIXES

    def load(self, path: Path, root: Path, kind: DocumentKind) -> Document:
        text = path.read_text(encoding="utf-8").lstrip("\ufeff")
        metadata: dict = {}
        if front := _FRONT_MATTER.match(text):
            metadata = yaml.safe_load(front.group(1)) or {}
            text = text[front.end():].lstrip()
        source = path.relative_to(root).as_posix()
        match = _TITLE.search(text)
        title = metadata.get("name") or (match.group(1).strip() if match else path.stem)
        return Document(id=f"{kind.value}/{source}", source=source, title=str(title), kind=kind, text=text,
                        metadata=metadata)

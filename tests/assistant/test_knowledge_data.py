"""Consistency of docs/knowledge: every document is findable (summary), refers to real MCP tools, and the
retrieval eval set only expects documents that exist."""

import re
from collections import Counter
from pathlib import Path

import pytest
import yaml

from src.assistant.domain.knowledge.document import DocumentKind
from src.assistant.infrastructure.knowledge.markdown_loader import MarkdownLoader

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "docs" / "knowledge"
MCP_TOOLS = ROOT / "apps" / "cloud" / "mcp_server" / "tools"
PREFIX = {DocumentKind.SKILL: "skill_", DocumentKind.RUNBOOK: "runbook_", DocumentKind.DOC: "doc_",
          DocumentKind.GUIDE: "guide_"}


def _documents():
    loader = MarkdownLoader()
    for kind in DocumentKind:
        folder = KNOWLEDGE / kind.value
        for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
            yield loader.load(path, folder, kind)


DOCUMENTS = list(_documents())


def _mcp_tool_names() -> set[str]:
    source = "\n".join(p.read_text(encoding="utf-8") for p in MCP_TOOLS.glob("*.py"))
    return set(re.findall(r"@mcp\.tool\(\)\s*\nasync def (\w+)", source))


def test_knowledge_base_is_not_empty():
    assert len(DOCUMENTS) >= 10


@pytest.mark.parametrize("document", DOCUMENTS, ids=lambda d: d.id)
def test_document_is_searchable_and_well_formed(document):
    meta = document.metadata
    assert len(document.summary) >= 200, "summary is the only searchable text: make it self-contained"
    assert meta.get("id", "").startswith(PREFIX[document.kind])
    assert document.title and not document.text.startswith("---")
    unknown = set(meta.get("tools", [])) - _mcp_tool_names()
    assert not unknown, f"not MCP tools: {unknown}"


def test_document_ids_are_unique():
    duplicated = [i for i, n in Counter(d.metadata["id"] for d in DOCUMENTS).items() if n > 1]
    assert not duplicated


def test_eval_queries_cover_every_document():
    queries = yaml.safe_load((ROOT / "evals" / "assistant" / "datasets" / "retrieval_queries.yaml").read_text(encoding="utf-8"))["queries"]
    known = {d.id for d in DOCUMENTS}
    for case in queries:
        assert set(case["expected"]) <= known, case
    covered = Counter(case["expected"][0] for case in queries)
    assert all(covered[doc_id] >= 3 for doc_id in known), covered

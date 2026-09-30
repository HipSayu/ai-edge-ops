import hashlib
import math

import pytest
from qdrant_client import AsyncQdrantClient

from src.assistant.bootstrap.knowledge_container import KnowledgeContainer
from src.assistant.config.knowledge_settings import KnowledgeSettings
from src.assistant.domain.knowledge.document import DocumentKind
from src.assistant.infrastructure.knowledge.qdrant_vector_store import QdrantVectorStore
from src.assistant.application.tools.knowledge_search import KnowledgeSearch

RUNBOOK = """---
id: runbook_camera_offline
name: Camera offline
tools: [get_runtime, control_runtime]
summary: Camera OFFLINE, no frames arrive. Restart the runtime, then check the RTSP url.
---

# Camera offline

## Fix
Restart the runtime with `POST /runtimes/{id}/restart`, then check the RTSP url.
"""

GUIDE = """---
name: Deploy a model
summary: Deploy a model to a node and wait for the deployment to be SUCCEEDED.
---

# Deploy a model

## Steps
Create a deployment for the node and wait for SUCCEEDED.
"""

NO_SUMMARY = """# Notes

Nothing to search this by.
"""


class BagOfWordsEmbedder:
    """Deterministic stand-in for OpenAI: hashed word counts, L2-normalised."""

    dimensions = 64

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    def _vector(self, text: str) -> list[float]:
        v = [0.0] * self.dimensions
        for word in text.lower().split():
            v[int(hashlib.md5(word.strip(".,`#").encode()).hexdigest(), 16) % self.dimensions] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]


def container_for(root, store) -> KnowledgeContainer:
    return KnowledgeContainer(KnowledgeSettings(knowledge_dir=root), embedder=BagOfWordsEmbedder(), store=store)


@pytest.fixture
async def knowledge(tmp_path):
    (tmp_path / "runbook").mkdir()
    (tmp_path / "runbook" / "camera-offline.md").write_text(RUNBOOK, encoding="utf-8")
    (tmp_path / "runbook" / "notes.txt").write_text("ignored", encoding="utf-8")
    (tmp_path / "runbook" / "no-summary.md").write_text(NO_SUMMARY, encoding="utf-8")
    (tmp_path / "guide").mkdir()
    (tmp_path / "guide" / "deploy.md").write_text(GUIDE, encoding="utf-8")
    (tmp_path / "eval").mkdir()  # not a DocumentKind folder: ignored
    (tmp_path / "eval" / "queries.md").write_text(GUIDE, encoding="utf-8")
    store = QdrantVectorStore(AsyncQdrantClient(location=":memory:"), "test_knowledge")
    container = container_for(tmp_path, store)
    yield container, tmp_path, store
    await container.close()


async def test_sync_embeds_summaries_and_skips_undescribed_documents(knowledge):
    container, _, _ = knowledge
    report = await container.ingestion_service.sync()
    assert sorted(report.ingested) == ["guide/deploy.md", "runbook/camera-offline.md"]
    assert report.skipped == ["runbook/no-summary.md"]

    again = await container.ingestion_service.sync()
    assert again.ingested == [] and sorted(again.unchanged) == ["guide/deploy.md", "runbook/camera-offline.md"]

    results = await container.retrieval_service.search("camera offline restart runtime")
    assert results[0].document.id == "runbook/camera-offline.md"
    assert results[0].citation == "camera-offline.md"
    assert "---" not in results[0].document.text and results[0].document.title == "Camera offline"

    only_guides = await container.retrieval_service.search("camera offline", kinds=[DocumentKind.GUIDE])
    assert {r.document.kind for r in only_guides} == {DocumentKind.GUIDE}


async def test_vector_store_keeps_ids_and_embeddings_only(knowledge):
    container, _, store = knowledge
    await container.ingestion_service.sync()
    points, _ = await store._client.scroll("test_knowledge", with_payload=True)
    assert {frozenset(p.payload) for p in points} == {frozenset({"document_id", "kind", "content_hash"})}


async def test_changed_documents_reingest_and_deleted_ones_are_removed(knowledge):
    container, root, store = knowledge
    await container.ingestion_service.sync()
    path = root / "runbook" / "camera-offline.md"
    path.write_text(RUNBOOK.replace("no frames arrive", "black screen"), encoding="utf-8")
    (root / "guide" / "deploy.md").unlink()

    report = await container_for(root, store).ingestion_service.sync()  # files are read once per container
    assert report.ingested == ["runbook/camera-offline.md"]
    assert report.removed == ["guide/deploy.md"]


async def test_search_knowledge_returns_best_match_in_full_and_activates_its_tools(knowledge):
    container, _, _ = knowledge
    await container.ingestion_service.sync()
    search = KnowledgeSearch(container.retrieval_service).tool()

    found = await search.ainvoke({"query": "rtsp url restart camera offline"})
    assert found["best_match"]["title"] == "Camera offline"
    assert "POST /runtimes/{id}/restart" in found["best_match"]["text"]
    assert "---" not in found["best_match"]["text"]
    assert [m["title"] for m in found["other_matches"]] == ["Deploy a model"]
    assert "text" not in found["other_matches"][0]
    assert found["activated_tools"] == ["get_runtime", "control_runtime"]

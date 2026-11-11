"""The VectorStore port over a Qdrant collection: one point per section of a regulation file."""

import uuid

from qdrant_client import QdrantClient, models

from cloud.domain.policy.regulation import Passage


class QdrantVectorStore:
    def __init__(self, client: QdrantClient, collection: str = "regulations") -> None:
        self._client = client
        self._collection = collection

    def digests(self) -> dict[str, str]:
        if not self._client.collection_exists(self._collection):
            return {}
        digests: dict[str, str] = {}
        offset = None
        while True:
            points, offset = self._client.scroll(
                self._collection, limit=256, offset=offset, with_payload=["source", "digest"], with_vectors=False,
            )
            digests.update({p.payload["source"]: p.payload["digest"] for p in points})
            if offset is None:
                return digests

    def replace(self, source: str, digest: str, passages: list[Passage], vectors: list[list[float]]) -> bool:
        reset = self._ensure_collection(len(vectors[0]))
        self.remove(source)
        self._client.upsert(self._collection, points=[
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}#{i}")), vector=vector,
                payload={"source": p.source, "heading": p.heading, "text": p.text, "digest": digest},
            )
            for i, (p, vector) in enumerate(zip(passages, vectors))
        ])
        return reset

    def remove(self, source: str) -> None:
        if self._client.collection_exists(self._collection):
            self._client.delete(self._collection, points_selector=models.FilterSelector(filter=models.Filter(
                must=[models.FieldCondition(key="source", match=models.MatchValue(value=source))],
            )))

    def search(self, vector: list[float], top_k: int, min_score: float = 0.0) -> list[Passage]:
        if not self._client.collection_exists(self._collection):
            return []
        hits = self._client.query_points(
            self._collection, query=vector, limit=top_k, score_threshold=min_score or None, with_payload=True,
        ).points
        return [Passage(h.payload["source"], h.payload["heading"], h.payload["text"], round(h.score, 3)) for h in hits]

    def _ensure_collection(self, size: int) -> bool:
        """Creates the collection, or recreates it (empty) when the vectors have another size. True if data was dropped."""
        reset = False
        if self._client.collection_exists(self._collection):
            if self._client.get_collection(self._collection).config.params.vectors.size == size:
                return False
            self._client.delete_collection(self._collection)
            reset = True
        self._client.create_collection(
            self._collection, vectors_config=models.VectorParams(size=size, distance=models.Distance.COSINE),
        )
        self._client.create_payload_index(self._collection, "source", models.PayloadSchemaType.KEYWORD)
        return reset

import uuid

from qdrant_client import AsyncQdrantClient, models

from src.assistant.domain.knowledge.document import Document, DocumentKind
from src.assistant.domain.knowledge.vector_hit import VectorHit


class QdrantVectorStore:
    """One Qdrant collection, cosine distance. A point is a document's vector with a minimal payload
    (document_id, kind, content_hash); no content: that stays in the local DocumentRepository."""

    def __init__(self, client: AsyncQdrantClient, collection: str) -> None:
        self._client = client
        self._collection = collection

    @staticmethod
    def point_id(document_id: str) -> str:
        # Deterministic UUID: re-ingesting the same document overwrites it in place
        return str(uuid.uuid5(uuid.NAMESPACE_URL, document_id))

    async def ensure_collection(self, dimensions: int) -> None:
        if await self._client.collection_exists(self._collection):
            info = await self._client.get_collection(self._collection)
            size = info.config.params.vectors.size
            if size != dimensions:
                raise ValueError(
                    f"Collection '{self._collection}' has {size}-d vectors but the embedder returns {dimensions}-d; "
                    "re-create it or use another collection name"
                )
            return
        await self._client.create_collection(
            self._collection,
            vectors_config=models.VectorParams(size=dimensions, distance=models.Distance.COSINE),
        )
        for name in ("document_id", "kind"):
            await self._client.create_payload_index(self._collection, name, models.PayloadSchemaType.KEYWORD)

    async def upsert(self, document: Document, vector: list[float]) -> None:
        payload = {"document_id": document.id, "kind": document.kind.value, "content_hash": document.content_hash}
        point = models.PointStruct(id=self.point_id(document.id), vector=vector, payload=payload)
        await self._client.upsert(self._collection, points=[point], wait=True)

    async def search(self, vector: list[float], limit: int, kinds: list[DocumentKind] | None = None) -> list[VectorHit]:
        query_filter = None
        if kinds:
            query_filter = models.Filter(
                must=[models.FieldCondition(key="kind", match=models.MatchAny(any=[k.value for k in kinds]))]
            )
        response = await self._client.query_points(
            self._collection, query=vector, limit=limit, query_filter=query_filter, with_payload=["document_id"]
        )
        return [VectorHit(p.payload["document_id"], p.score) for p in response.points]

    async def document_hash(self, document_id: str) -> str | None:
        points = await self._client.retrieve(
            self._collection, ids=[self.point_id(document_id)], with_payload=["content_hash"]
        )
        return points[0].payload.get("content_hash") if points else None

    async def document_ids(self) -> set[str]:
        ids: set[str] = set()
        offset = None
        while True:
            points, offset = await self._client.scroll(
                self._collection, limit=256, offset=offset, with_payload=["document_id"], with_vectors=False
            )
            ids.update(p.payload["document_id"] for p in points)
            if offset is None:
                return ids

    async def delete(self, document_ids: list[str]) -> None:
        if document_ids:
            selector = models.PointIdsList(points=[self.point_id(d) for d in document_ids])
            await self._client.delete(self._collection, points_selector=selector, wait=True)

    async def ping(self) -> bool:
        try:
            await self._client.get_collections()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.close()

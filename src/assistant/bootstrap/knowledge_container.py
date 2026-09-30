from qdrant_client import AsyncQdrantClient

from src.assistant.config.knowledge_settings import KnowledgeSettings
from src.assistant.application.ports.embedder import Embedder
from src.assistant.infrastructure.embedding.embedder_factory import EmbedderFactory
from src.assistant.infrastructure.knowledge.markdown_loader import MarkdownLoader
from src.assistant.infrastructure.knowledge.local_document_repository import LocalDocumentRepository
from src.assistant.infrastructure.knowledge.qdrant_vector_store import QdrantVectorStore
from src.assistant.application.ports.document_repository import DocumentRepository
from src.assistant.application.ports.vector_store import VectorStore
from src.assistant.application.services.ingestion_service import IngestionService
from src.assistant.application.services.retrieval_service import RetrievalService


class KnowledgeContainer:
    """Wires the RAG pipeline. Shared by the assistant (retrieval) and the ingest CLI (ingestion).

    Content is read from local files (settings.knowledge_dir); Qdrant holds only the embeddings.
    """

    def __init__(
        self,
        settings: KnowledgeSettings,
        embedder: Embedder | None = None,
        store: VectorStore | None = None,
        documents: DocumentRepository | None = None,
    ) -> None:
        self.documents = documents or LocalDocumentRepository(settings.knowledge_dir, [MarkdownLoader()])
        self.embedder = embedder or EmbedderFactory.create(settings)
        self.store = store or QdrantVectorStore(
            AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key), settings.qdrant_collection
        )
        self.ingestion_service = IngestionService(self.documents, self.embedder, self.store)
        self.retrieval_service = RetrievalService(
            self.embedder, self.store, self.documents, settings.knowledge_top_k, settings.knowledge_min_score
        )

    async def close(self) -> None:
        await self.store.close()

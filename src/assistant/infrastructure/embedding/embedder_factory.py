from src.assistant.config.knowledge_settings import KnowledgeSettings
from src.assistant.application.ports.embedder import Embedder


class EmbedderFactory:
    """The embedder named by settings; shared by knowledge retrieval and tool search."""

    @staticmethod
    def create(settings: KnowledgeSettings) -> Embedder:
        if settings.embedding_provider == "sentence_transformers":
            from src.assistant.infrastructure.embedding.sentence_transformer_embedder import (
                SentenceTransformerEmbedder,
                vietnamese_word_segmenter,
            )

            segmenter = vietnamese_word_segmenter() if settings.embedding_vi_word_segment else None
            return SentenceTransformerEmbedder(settings.embedding_model, settings.embedding_device, segmenter)

        from src.assistant.infrastructure.embedding.openai_embedder import OpenAIEmbedder

        return OpenAIEmbedder(
            settings.embedding_model, settings.embedding_dimensions,
            api_key=settings.embedding_api_key, base_url=settings.embedding_base_url,
        )

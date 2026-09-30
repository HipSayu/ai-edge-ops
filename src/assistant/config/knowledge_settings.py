from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class KnowledgeSettings(BaseSettings):
    """RAG over docs/guides/skills/runbooks: embeddings (OpenAI or a local model) + Qdrant."""

    knowledge_enabled: bool = False
    # Document content: <knowledge_dir>/<kind>/*.md, read locally. Qdrant stores only their embeddings.
    knowledge_dir: Path = Path("docs/knowledge")

    # openai: hosted API. sentence_transformers: local model, e.g. dangvantuan/vietnamese-embedding
    embedding_provider: Literal["openai", "sentence_transformers"] = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536  # openai only; a local model reports its own
    # sentence_transformers only: cpu | cuda (None = auto), and pyvi word segmentation for PhoBERT-based models
    embedding_device: str | None = None
    embedding_vi_word_segment: bool = False
    embedding_api_key: str | None = None  # None falls back to OPENAI_API_KEY
    embedding_base_url: str | None = None

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "assistant_knowledge"

    knowledge_top_k: int = 5
    knowledge_min_score: float = 0.0

import asyncio
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def vietnamese_word_segmenter() -> Callable[[str], str]:
    """pyvi word segmentation ("học sinh" -> "học_sinh"), which PhoBERT-based models expect as input."""
    from pyvi.ViTokenizer import tokenize

    return tokenize


class SentenceTransformerEmbedder:
    """Local embeddings with a sentence-transformers model, e.g. dangvantuan/vietnamese-embedding.

    The model loads on first use (download + load take a while) and runs in a worker thread.
    Vectors are L2-normalised for cosine search; `dimensions` comes from the model itself.
    """

    def __init__(
        self,
        model: str = "dangvantuan/vietnamese-embedding",
        device: str | None = None,
        segmenter: Callable[[str], str] | None = None,
        batch_size: int = 32,
    ) -> None:
        self._model_name = model
        self._device = device
        self._segmenter = segmenter
        self._batch_size = batch_size
        self._model: Any = None

    @property
    def _loaded(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model %s", self._model_name)
            model = SentenceTransformer(self._model_name, device=self._device)
            # Some checkpoints (PhoBERT: 258 positions, 2 reserved) declare a longer max_seq_length than
            # the position table holds, which crashes on long inputs instead of truncating them.
            positions = getattr(getattr(model[0], "auto_model", None), "config", None)
            positions = getattr(positions, "max_position_embeddings", None)
            if positions and (model.max_seq_length is None or model.max_seq_length > positions - 2):
                model.max_seq_length = positions - 2
            self._model = model
        return self._model

    @property
    def max_tokens(self) -> int | None:
        """Longer inputs are truncated: keep summaries within this many tokens."""
        return self._loaded.max_seq_length

    @property
    def dimensions(self) -> int:
        return self._loaded.get_sentence_embedding_dimension()

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._encode, texts)

    async def embed_query(self, text: str) -> list[float]:
        return (await self.embed_documents([text]))[0]

    def _encode(self, texts: list[str]) -> list[list[float]]:
        if self._segmenter is not None:
            texts = [self._segmenter(t) for t in texts]
        vectors = self._loaded.encode(
            texts, batch_size=self._batch_size, normalize_embeddings=True, convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

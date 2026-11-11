import httpx

from shared.errors import ServiceUnavailable


class HttpEmbedder:
    """The Embedder port over any OpenAI-compatible `/v1/embeddings` endpoint (the `embedding` container, vLLM, Ollama,
    OpenAI...). Nothing is connected until the first call."""

    def __init__(self, base_url: str, model: str, api_key: str | None = None, timeout_sec: float = 60.0) -> None:
        self._url = base_url.rstrip("/") + "/embeddings"
        self._model = model
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._timeout = timeout_sec
        self.name = f"{base_url}|{model}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for batch in self._batches(texts):
            vectors += self._embed(batch)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]

    @staticmethod
    def _batches(texts: list[str], size: int = 32) -> list[list[str]]:
        return [texts[i : i + size] for i in range(0, len(texts), size)]

    def _embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = httpx.post(
                self._url, json={"model": self._model, "input": texts}, headers=self._headers, timeout=self._timeout
            )
            response.raise_for_status()
            rows = sorted(response.json()["data"], key=lambda row: row["index"])
        except (httpx.HTTPError, KeyError, ValueError) as e:
            raise ServiceUnavailable(f"Không gọi được bộ nhúng văn bản: {e}") from e
        return [row["embedding"] for row in rows]

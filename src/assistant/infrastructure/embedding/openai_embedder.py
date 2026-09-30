from openai import AsyncOpenAI


class OpenAIEmbedder:
    """OpenAI embeddings (text-embedding-3-*). `dimensions` shortens the vector natively for v3 models."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        api_key: str | None = None,
        base_url: str | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        # api_key None falls back to OPENAI_API_KEY
        self._client = client or AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self._client.embeddings.create(model=self._model, input=texts, dimensions=self._dimensions)
        return [item.embedding for item in sorted(response.data, key=lambda d: d.index)]

    async def embed_query(self, text: str) -> list[float]:
        return (await self.embed_documents([text]))[0]

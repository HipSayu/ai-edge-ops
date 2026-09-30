from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

from src.assistant.application.ports.embedder import Embedder
from src.assistant.application.helpers.vectors import cosine
from src.assistant.application.tools.registry import ToolRegistry

ACTIVATED_KEY = "activated_tools"


class ToolIndex:
    """Embedding index over tool names + descriptions, built once at startup (tools are few)."""

    def __init__(self, embedder: Embedder, tools: list[BaseTool]) -> None:
        self._embedder = embedder
        self._tools = tools
        self._vectors: list[list[float]] = []

    @staticmethod
    def text(tool: BaseTool) -> str:
        return f"{tool.name.replace('_', ' ')}: {tool.description}"

    async def build(self) -> None:
        self._vectors = await self._embedder.embed_documents([self.text(t) for t in self._tools])

    async def search(self, query: str, limit: int = 5) -> list[tuple[BaseTool, float]]:
        if not self._tools:
            return []
        q = await self._embedder.embed_query(query)
        scored = [(tool, cosine(q, v)) for tool, v in zip(self._tools, self._vectors)]
        return sorted(scored, key=lambda pair: pair[1], reverse=True)[:limit]


class SearchToolsArgs(BaseModel):
    query: str = Field(description="Việc cần làm, mô tả bằng tiếng Việt tự nhiên (vd 'lấy nhiệt độ GPU của node')")
    limit: int = Field(default=5, ge=1, le=10, description="Số tool tối đa trả về")


class ToolSearch:
    """The `search_tools` tool: finds fleet tools by description and activates them for the next step."""

    def __init__(self, index: ToolIndex) -> None:
        self._index = index

    def tool(self) -> BaseTool:
        return StructuredTool.from_function(
            coroutine=self._search, name="search_tools", args_schema=SearchToolsArgs,
            description=(
                "Tìm tool thao tác hệ thống edge (cluster, node, runtime, deployment, telemetry, event) theo mô tả. "
                "Các tool tìm được sẽ được kích hoạt và gọi được từ bước tiếp theo."
            ),
        )

    async def _search(self, query: str, limit: int = 5) -> dict:
        try:
            found = await self._index.search(query, limit)
        except Exception as exc:  # embedding backend down: tell the model instead of failing the turn
            return {"error": "tool_search_unavailable", "detail": str(exc)}
        return {
            "tools": [
                {"name": tool.name, "description": tool.description, "score": round(score, 3),
                 "requires_approval": ToolRegistry.is_write(tool.name)}
                for tool, score in found
            ],
            ACTIVATED_KEY: [tool.name for tool, _ in found],
        }

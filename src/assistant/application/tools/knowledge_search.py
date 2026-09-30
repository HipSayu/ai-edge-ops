from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

from src.assistant.domain.knowledge.document import DocumentKind
from src.assistant.application.services.retrieval_service import RetrievalService
from src.assistant.application.tools.tool_search import ACTIVATED_KEY


class SearchKnowledgeArgs(BaseModel):
    query: str = Field(description="Tình huống hoặc câu hỏi, viết bằng tiếng Việt tự nhiên")
    kind: DocumentKind | None = Field(default=None, description="Giới hạn loại: skill, runbook hoặc doc")


class KnowledgeSearch:
    """The `search_knowledge` tool. Documents are matched by summary; the best match comes back in full,
    the next ones as summaries. A matched skill/runbook also activates the tools its procedure uses.
    """

    def __init__(self, retrieval: RetrievalService, limit: int = 3) -> None:
        self._retrieval = retrieval
        self._limit = limit

    def tool(self) -> BaseTool:
        return StructuredTool.from_function(
            coroutine=self._search, name="search_knowledge", args_schema=SearchKnowledgeArgs,
            description=(
                "Tìm quy trình xử lý (skill), runbook sự cố và tài liệu tra cứu (ngưỡng metric, ý nghĩa trạng thái). "
                "Dùng trước khi xử lý việc phức tạp cần nhiều bước/nhiều tool. Trả về toàn văn tài liệu khớp nhất; "
                "các tool mà quy trình đó dùng được kích hoạt sẵn."
            ),
        )

    async def _search(self, query: str, kind: DocumentKind | None = None) -> dict[str, Any]:
        try:
            results = await self._retrieval.search(query, [kind] if kind else None, limit=self._limit)
        except Exception as exc:  # surface to the model, don't crash the graph
            return {"error": "knowledge_unavailable", "detail": str(exc)}
        if not results:
            return {"results": [], ACTIVATED_KEY: []}
        best, others = results[0].document, results[1:]
        return {
            "best_match": {
                "title": best.title, "kind": best.kind.value, "citation": results[0].citation,
                "score": round(results[0].score, 3), "text": best.text,
            },
            "other_matches": [
                {"title": r.document.title, "kind": r.document.kind.value, "score": round(r.score, 3),
                 "summary": r.document.summary}
                for r in others
            ],
            ACTIVATED_KEY: list(best.tools),
        }

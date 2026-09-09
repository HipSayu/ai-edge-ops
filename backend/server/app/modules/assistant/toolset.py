"""The same domain tools as the MCP server (:data:`app.mcp.ALL_TOOLS`), wrapped
as LangChain tools for the in-process operator assistant."""

from __future__ import annotations

from langchain_core.tools import BaseTool, StructuredTool

from app.mcp.tools import ALL_TOOLS


def langchain_tools() -> list[BaseTool]:
    return [
        StructuredTool.from_function(
            coroutine=fn,
            name=fn.__name__,
            description=(fn.__doc__ or fn.__name__).strip(),
        )
        for fn in ALL_TOOLS
    ]


__all__ = ["langchain_tools"]

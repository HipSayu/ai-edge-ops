"""Every MCP tool opens its own short DB session — the tools are self-contained
read (mostly) helpers, not part of a request transaction."""

from __future__ import annotations

from app.core.database import session_scope

__all__ = ["session_scope"]

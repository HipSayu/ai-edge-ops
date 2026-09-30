from typing import Any, Protocol

from langchain_core.callbacks import BaseCallbackHandler


class Tracer(Protocol):
    """Traces one chat turn: callbacks attached to the graph run, plus the run metadata they read."""

    def callbacks(self) -> list[BaseCallbackHandler]: ...

    def metadata(self, session_id: str, user_id: str | None, kind: str) -> dict[str, Any]: ...

    def shutdown(self) -> None:
        """Flushes buffered traces; call on application stop."""
        ...

from collections.abc import Iterable

from langchain_core.tools import BaseTool

# Tools that change fleet state: run only after the user approves each call (human in the loop)
WRITE_PREFIXES = ("create_", "update_", "remove_", "register_", "control_")


class ToolRegistry:
    """Every tool the agent may call.

    `core` tools (search_tools, search_knowledge) are bound on every model call. The others are
    discoverable: bound only once activated, by search_tools or by a matching skill, so the prompt
    carries the schemas it needs rather than all of them.
    """

    def __init__(self, core: list[BaseTool], discoverable: list[BaseTool]) -> None:
        self._core = list(core)
        self._discoverable = {tool.name: tool for tool in discoverable}

    @property
    def discoverable(self) -> list[BaseTool]:
        return list(self._discoverable.values())

    def all(self) -> list[BaseTool]:
        return [*self._core, *self._discoverable.values()]

    def bound(self, active: Iterable[str]) -> list[BaseTool]:
        """Core tools plus the activated ones, in a stable order."""
        wanted = set(active)
        return [*self._core, *(tool for name, tool in self._discoverable.items() if name in wanted)]

    def known(self, names: Iterable[str]) -> list[str]:
        """The discoverable tool names among `names` (unknown or core names dropped)."""
        return [name for name in names if name in self._discoverable]

    @staticmethod
    def is_write(name: str) -> bool:
        return name.startswith(WRITE_PREFIXES)

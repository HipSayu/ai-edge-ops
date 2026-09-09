"""Discovers the domain modules and wires their startup side effects.

Two things every ``app.modules.<context>`` package may contribute:

1. ``models`` — importing it registers ORM classes on ``Base.metadata``.
2. ``subscribers`` — a module exposing ``register()`` that subscribes the
   context's handlers to :data:`app.core.events.event_bus`.

Both are optional per module and found by name, so adding a module needs no
edit here.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil

logger = logging.getLogger(__name__)


class ModuleRegistry:
    def __init__(self, package: str = "app.modules") -> None:
        self._package = package
        self._subscribers_registered = False

    def _context_names(self) -> list[str]:
        pkg = importlib.import_module(self._package)
        return sorted(
            name
            for _, name, is_pkg in pkgutil.iter_modules(pkg.__path__)
            if is_pkg
        )

    def _try_import(self, context: str, submodule: str):
        try:
            return importlib.import_module(f"{self._package}.{context}.{submodule}")
        except ModuleNotFoundError as exc:
            if exc.name == f"{self._package}.{context}.{submodule}":
                return None
            raise

    def load_models(self) -> None:
        """Import every ``<context>.models`` so ``Base.metadata`` is complete."""
        for context in self._context_names():
            self._try_import(context, "models")

    def register_subscribers(self) -> None:
        """Call ``<context>.subscribers.register()`` wherever it exists."""
        if self._subscribers_registered:
            return
        for context in self._context_names():
            module = self._try_import(context, "subscribers")
            if module is None:
                continue
            register = getattr(module, "register", None)
            if register is None:
                logger.warning("%s.subscribers has no register()", context)
                continue
            register()
            logger.debug("registered subscribers for %s", context)
        self._subscribers_registered = True

    def reset(self) -> None:
        """Test helper: allow :meth:`register_subscribers` to run again."""
        self._subscribers_registered = False


__all__ = ["ModuleRegistry"]

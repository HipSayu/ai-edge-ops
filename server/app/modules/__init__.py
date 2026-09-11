"""Domain modules.

Importing this package must populate ``Base.metadata`` (every ORM model) and
lets the app wire cross-module event subscribers. Both are delegated to
:class:`app.modules.registry.ModuleRegistry`.
"""

from __future__ import annotations

from app.modules.registry import ModuleRegistry

_registry = ModuleRegistry()
_registry.load_models()


def register_event_handlers() -> None:
    _registry.register_subscribers()


def reset_event_handlers() -> None:
    """Test helper."""
    _registry.reset()


__all__ = ["register_event_handlers", "reset_event_handlers"]

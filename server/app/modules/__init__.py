"""Module registry.

Importing this package has two side effects required at startup:
1. every ORM model is imported, so ``Base.metadata`` knows all tables;
2. :func:`register_event_handlers` wires cross-module event subscribers.
"""

from __future__ import annotations

from app.modules.deployment import models as _deployment_models  # noqa: F401
from app.modules.fleet import models as _fleet_models  # noqa: F401
from app.modules.model_registry import models as _model_registry_models  # noqa: F401
from app.modules.observability import models as _observability_models  # noqa: F401

_HANDLERS_REGISTERED = False


def register_event_handlers() -> None:
    global _HANDLERS_REGISTERED
    if _HANDLERS_REGISTERED:
        return
    from app.modules.fleet import events as fleet_events
    from app.modules.observability import events as observability_events

    fleet_events.register()
    observability_events.register()
    _HANDLERS_REGISTERED = True

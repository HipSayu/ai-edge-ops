"""Module registry.

Importing this package has two side effects required at startup:
1. every ORM model is imported, so ``Base.metadata`` knows all tables;
2. :func:`register_event_handlers` wires cross-module event subscribers.
"""

from __future__ import annotations

from app.modules.assistant import models as _assistant_models  # noqa: F401
from app.modules.access_control import models as _access_control_models  # noqa: F401
from app.modules.camera import models as _camera_models  # noqa: F401
from app.modules.deployment import models as _deployment_models  # noqa: F401
from app.modules.agent import models as _agent_models  # noqa: F401
from app.modules.model_registry import models as _model_registry_models  # noqa: F401
from app.modules.observability import models as _observability_models  # noqa: F401
from app.modules.system import models as _system_models  # noqa: F401
from app.modules.user import models as _user_models  # noqa: F401

_HANDLERS_REGISTERED = False


def register_event_handlers() -> None:
    global _HANDLERS_REGISTERED
    if _HANDLERS_REGISTERED:
        return
    from app.modules.agent import handlers as agent_handlers
    from app.modules.agent import telemetry_relay as agent_ws_relay
    from app.modules.observability import integration as observability_handlers
    from app.modules.observability import realtime as observability_ws_relay

    agent_handlers.register()
    agent_ws_relay.register()
    observability_handlers.register()
    observability_ws_relay.register()
    _HANDLERS_REGISTERED = True

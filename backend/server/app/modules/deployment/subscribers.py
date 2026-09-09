"""Deployment reacts to config changes — re-resolve and push to the device."""

from __future__ import annotations

from app.core.database import session_scope
from app.core.events import event_bus
from app.modules.agent.event import DeviceConfigChanged
from app.modules.agent.service import AgentService
from app.modules.deployment.config_resolver import ConfigResolver
from app.modules.deployment.event import ConfigResolved


class DeploymentSubscribers:
    def register(self) -> None:
        event_bus.subscribe(DeviceConfigChanged, self._on_config_changed)

    async def _on_config_changed(self, event: DeviceConfigChanged) -> None:
        async with session_scope() as session:
            device = await AgentService(session).get_device(event.device_id)
            config = await ConfigResolver(session).resolve_update(device)
        await event_bus.publish(ConfigResolved(device_id=event.device_id, config=config))


def register() -> None:
    DeploymentSubscribers().register()


__all__ = ["DeploymentSubscribers", "register"]

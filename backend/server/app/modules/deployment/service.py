"""Deploy use-case: resolve the image, set the device's desired state, fire the
command. No deployment table — the current state is `Device.desired_image` vs the
FleetRegistry's reported `active_image`; history is in `audit_logs`.
"""

from __future__ import annotations

from dqh.svc_core.contracts.errors import AppError, NotFoundError
from dqh.svc_core.helpers.time import utcnow
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import event_bus
from app.core.model_catalog import model_catalog
from app.modules.agent import AgentService
from app.modules.deployment.event import DeployRequested
from app.modules.deployment.schemas import DeploymentView, DeployRequest
from app.modules.system.models import AuditLog


class DeployService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.agent = AgentService(session)

    async def deploy(self, data: DeployRequest, *, actor: str = "system") -> DeploymentView:
        device = await self.agent.get_device(data.device_id)  # 404 if missing
        tag = data.image if "@" in data.image else data.image.rsplit(":", 1)[-1]
        try:
            image = await model_catalog.get_model(tag)
        except AppError as exc:
            raise NotFoundError(f"model image {data.image!r} not in the registry") from exc

        device.desired_image = image.pinned_ref
        if data.config:
            device.inference = {**device.inference, **data.config}
        self.session.add(
            AuditLog(
                action="deploy.model",
                actor=actor,
                detail=f"{device.device_id} -> {image.pinned_ref}",
                created_at=utcnow().isoformat(),
            )
        )
        await self.session.commit()
        await event_bus.publish(
            DeployRequested(device_id=device.device_id, image=image.pinned_ref, config=data.config)
        )
        return await self._view(device.device_id)

    async def list(self) -> list[DeploymentView]:
        return [v async for v in self._iter_views() if v.desired_image is not None]

    async def count_active(self) -> int:
        return sum([1 async for v in self._iter_views() if v.in_sync])

    # --- internals ---------------------------------------------------------
    async def _iter_views(self):
        for d in await self.agent.list_devices(site=None):
            yield DeploymentView(
                device_id=d.device_id,
                name=d.name,
                desired_image=d.desired_image,
                active_image=d.active_image,
                runtime_status=d.runtime_status,
                in_sync=d.in_sync,
                updated_at=d.last_seen_at,
            )

    async def _view(self, device_id: str) -> DeploymentView:
        async for v in self._iter_views():
            if v.device_id == device_id:
                return v
        raise NotFoundError(f"device {device_id} not found")


__all__ = ["DeployService"]

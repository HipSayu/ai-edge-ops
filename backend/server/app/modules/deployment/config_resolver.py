"""Resolve the effective inference config for a device.

Layered, lowest priority first:

    1. model defaults   - ai.edge-ops.model.{conf,iou,imgsz,classes} image labels
    2. global policy     - app_settings["inference_policy"] (fleet-wide)
    3. per-device        - Device.inference (sparse operator overrides)

The agent gets the merged dict; it never merges anything itself.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent.models import Device
from app.modules.model_registry.schemas import ModelImage
from app.modules.system.service import SystemService


class ConfigResolver:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve(self, image: ModelImage, device: Device, *, extra: dict | None = None) -> dict:
        effective: dict = {}
        if image.conf is not None:
            effective["conf_threshold"] = image.conf
        if image.iou is not None:
            effective["iou_threshold"] = image.iou
        if image.imgsz is not None:
            effective["imgsz"] = image.imgsz
        if image.classes:
            effective["classes"] = image.classes

        _merge(effective, await self._policy())
        _merge(effective, device.inference or {})
        _merge(effective, extra or {})
        return effective

    async def resolve_update(self, device: Device) -> dict:
        """Config-only refresh (no model change): global policy + per-device."""
        effective: dict = {}
        _merge(effective, await self._policy())
        _merge(effective, device.inference or {})
        return effective

    async def _policy(self) -> dict:
        return await SystemService(self.session).get_setting("inference_policy") or {}


def _merge(base: dict, overrides: dict) -> None:
    for k, v in overrides.items():
        if v is not None:
            base[k] = v


__all__ = ["ConfigResolver"]

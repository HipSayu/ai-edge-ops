"""The shared :class:`ModelCatalog` instance — one per process."""

from __future__ import annotations

from app.core.config import settings
from app.modules.model_registry.catalog import ModelCatalog

model_catalog = ModelCatalog(settings.model_registry)

__all__ = ["model_catalog"]

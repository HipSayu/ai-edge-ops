"""Model registry context — the catalog is read live from an OCI registry
(GHCR), there is no local DB. See :class:`ModelCatalog`.
"""

from __future__ import annotations

from app.modules.model_registry.catalog import ModelCatalog
from app.modules.model_registry.schemas import ModelImage

__all__ = ["ModelCatalog", "ModelImage"]

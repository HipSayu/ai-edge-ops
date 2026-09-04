"""Model registry context: models and their versioned, compressed artifacts.

Public surface for other modules: :class:`ModelRegistryService`.
"""

from __future__ import annotations

from app.modules.model_registry.service import ModelRegistryService

__all__ = ["ModelRegistryService"]

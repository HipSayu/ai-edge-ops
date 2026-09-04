"""Deployment context: binding a published model version to an edge device.

Public surface for other modules: :class:`DeploymentService`.
"""

from __future__ import annotations

from app.modules.deployment.service import DeploymentService

__all__ = ["DeploymentService"]

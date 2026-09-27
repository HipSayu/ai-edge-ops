"""Deployment context — deploy is a command; state = desired vs reported.

Public surface: :class:`DeployService`.
"""

from __future__ import annotations

from app.modules.deployment.service import DeployService

__all__ = ["DeployService"]

"""The shared :class:`FleetRegistry` instance — one per process, in-memory."""

from __future__ import annotations

from app.modules.agent.fleet_registry import FleetRegistry

fleet = FleetRegistry()

__all__ = ["fleet"]

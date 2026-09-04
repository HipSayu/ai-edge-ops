"""Aggregates every module router under the versioned API prefix."""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.deployment.router import router as deployment_router
from app.modules.fleet.router import router as fleet_router
from app.modules.model_registry.router import router as model_registry_router
from app.modules.observability.router import router as observability_router

api_router = APIRouter()
api_router.include_router(fleet_router)
api_router.include_router(model_registry_router)
api_router.include_router(deployment_router)
api_router.include_router(observability_router)

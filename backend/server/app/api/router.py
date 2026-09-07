"""Aggregates every module router under the versioned API prefix."""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.assistant.router import router as assistant_router
from app.modules.camera.router import router as camera_router
from app.modules.deployment.router import router as deployment_router
from app.modules.agent.router import router as agent_router
from app.modules.model_registry.router import router as model_registry_router
from app.modules.observability.router import router as observability_router
from app.modules.streaming.router import router as streaming_router
from app.modules.system.router import router as system_router
from app.modules.user.router import router as user_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(agent_router)
api_router.include_router(model_registry_router)
api_router.include_router(deployment_router)
api_router.include_router(observability_router)
api_router.include_router(camera_router)
api_router.include_router(streaming_router)
api_router.include_router(system_router)
api_router.include_router(assistant_router)
api_router.include_router(user_router)

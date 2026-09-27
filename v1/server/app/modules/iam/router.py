"""IAM HTTP surface: the user CRUD and auth sub-routers under one include."""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.iam.auth_router import router as _auth_router
from app.modules.iam.user_router import router as _user_router

router = APIRouter()
router.include_router(_user_router)
router.include_router(_auth_router)

__all__ = ["router"]

"""Model catalog HTTP endpoints — served straight from the OCI registry."""

from __future__ import annotations

import httpx
from dqh.svc_core.contracts.errors import NotFoundError
from dqh.svc_core.transports.http import ApiResponse, ok
from fastapi import APIRouter

from app.core.model_catalog import model_catalog
from app.modules.model_registry.catalog import ModelImage

router = APIRouter(prefix="/models", tags=["model-registry"])


@router.get("", response_model=ApiResponse[list[ModelImage]])
async def list_models(refresh: bool = False) -> ApiResponse[list[ModelImage]]:
    return ok(await model_catalog.list_models(refresh=refresh))


@router.get("/{tag}", response_model=ApiResponse[ModelImage])
async def get_model(tag: str, refresh: bool = False) -> ApiResponse[ModelImage]:
    try:
        return ok(await model_catalog.get_model(tag, refresh=refresh))
    except httpx.HTTPStatusError as exc:
        raise NotFoundError(f"model image {tag!r} not found") from exc

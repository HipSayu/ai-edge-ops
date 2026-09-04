"""Model registry HTTP endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Body, status

from app.api.deps import DbSession, Pagination
from app.core.pagination import Page
from app.modules.model_registry.domain import ModelTask, ModelVersionStatus
from app.modules.model_registry.schemas import (
    ModelCreate,
    ModelOut,
    ModelVersionCreate,
    ModelVersionOut,
    ModelWithVersions,
)
from app.modules.model_registry.service import ModelRegistryService

router = APIRouter(prefix="/models", tags=["model-registry"])


@router.post("", response_model=ModelOut, status_code=status.HTTP_201_CREATED)
async def create_model(data: ModelCreate, db: DbSession) -> ModelOut:
    return ModelOut.model_validate(await ModelRegistryService(db).create_model(data))


@router.get("", response_model=Page[ModelOut])
async def list_models(
    db: DbSession, params: Pagination, task: ModelTask | None = None
) -> Page[ModelOut]:
    page = await ModelRegistryService(db).list_models(task=task, params=params)
    return Page.build([ModelOut.model_validate(m) for m in page.items], page.total, params)


@router.get("/{model_id}", response_model=ModelWithVersions)
async def get_model(model_id: int, db: DbSession) -> ModelWithVersions:
    return ModelWithVersions.model_validate(await ModelRegistryService(db).get_model(model_id))


@router.post(
    "/{model_id}/versions",
    response_model=ModelVersionOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_version(
    model_id: int, data: ModelVersionCreate, db: DbSession
) -> ModelVersionOut:
    version = await ModelRegistryService(db).add_version(model_id, data)
    return ModelVersionOut.model_validate(version)


@router.post("/versions/{version_id}/status", response_model=ModelVersionOut)
async def transition_version(
    version_id: int,
    db: DbSession,
    target: ModelVersionStatus = Body(embed=True),
) -> ModelVersionOut:
    version = await ModelRegistryService(db).transition_version(version_id, target)
    return ModelVersionOut.model_validate(version)

"""Model registry use-cases."""

from __future__ import annotations

from dqh.svc_core.errors import BadRequestError as BusinessRuleError
from dqh.svc_core.errors import ConflictError, NotFoundError
from dqh.svc_core.http import Page
from dqh.svc_core.http import PaginationParams as PageParams
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.model_registry.domain import ModelTask, ModelVersionStatus
from app.modules.model_registry.models import Model, ModelVersion
from app.modules.model_registry.repository import ModelRepository, ModelVersionRepository
from app.modules.model_registry.schemas import ModelCreate, ModelVersionCreate

_STATUS_FLOW: dict[ModelVersionStatus, set[ModelVersionStatus]] = {
    ModelVersionStatus.DRAFT: {ModelVersionStatus.VALIDATED, ModelVersionStatus.ARCHIVED},
    ModelVersionStatus.VALIDATED: {ModelVersionStatus.PUBLISHED, ModelVersionStatus.ARCHIVED},
    ModelVersionStatus.PUBLISHED: {ModelVersionStatus.ARCHIVED},
    ModelVersionStatus.ARCHIVED: set(),
}


class ModelRegistryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.models = ModelRepository(session)
        self.versions = ModelVersionRepository(session)

    async def create_model(self, data: ModelCreate) -> Model:
        if await self.models.get_by_name(data.name):
            raise ConflictError(f"model '{data.name}' already exists")
        model = Model(**data.model_dump())
        await self.models.add(model)
        await self.session.commit()
        return model

    async def get_model(self, model_id: int) -> Model:
        model = await self.models.get_with_versions(model_id)
        if model is None:
            raise NotFoundError(f"model {model_id} not found")
        return model

    async def list_models(self, *, task: ModelTask | None, params: PageParams) -> Page[Model]:
        items, total = await self.models.list_page(task=task, params=params)
        return Page.of(items, total=total, params=params)

    async def add_version(self, model_id: int, data: ModelVersionCreate) -> ModelVersion:
        await self.get_model(model_id)
        if await self.versions.exists(model_id, data.version):
            raise ConflictError(f"version '{data.version}' already exists for model {model_id}")
        version = ModelVersion(model_id=model_id, **data.model_dump())
        await self.versions.add(version)
        await self.session.commit()
        return version

    async def get_version(self, version_id: int) -> ModelVersion:
        version = await self.versions.get(version_id)
        if version is None:
            raise NotFoundError(f"model version {version_id} not found")
        return version

    async def transition_version(
        self, version_id: int, target: ModelVersionStatus
    ) -> ModelVersion:
        version = await self.get_version(version_id)
        if target not in _STATUS_FLOW[version.status]:
            raise BusinessRuleError(
                f"cannot move version from {version.status} to {target}"
            )
        version.status = target
        await self.session.commit()
        return version

    async def ensure_deployable(self, version_id: int) -> ModelVersion:
        """Called by the deployment module before wiring a version to a device."""
        version = await self.get_version(version_id)
        if version.status is not ModelVersionStatus.PUBLISHED:
            raise BusinessRuleError(
                f"model version {version_id} is {version.status}, must be published to deploy"
            )
        return version

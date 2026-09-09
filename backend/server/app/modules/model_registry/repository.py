"""Model registry data access."""

from __future__ import annotations

from dqh.svc_core.persistence.sqlalchemy import BaseRepository
from dqh.svc_core.transports.http import PaginationParams as PageParams
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.model_registry.domain import ModelTask
from app.modules.model_registry.models import Model, ModelVersion


class ModelRepository(BaseRepository[Model]):
    model = Model

    async def get_with_versions(self, model_id: int) -> Model | None:
        stmt = (
            select(Model).where(Model.id == model_id).options(selectinload(Model.versions))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_name(self, name: str) -> Model | None:
        return (
            await self.session.execute(select(Model).where(Model.name == name))
        ).scalar_one_or_none()

    async def list_page(
        self, *, task: ModelTask | None, params: PageParams
    ) -> tuple[list[Model], int]:
        clauses = [Model.task == task] if task else []
        items = await self.list(*clauses, order_by=Model.name, params=params)
        total = await self.count(*clauses)
        return items, total


class ModelVersionRepository(BaseRepository[ModelVersion]):
    model = ModelVersion

    async def get_in_model(self, model_id: int, version_id: int) -> ModelVersion | None:
        stmt = select(ModelVersion).where(
            ModelVersion.id == version_id, ModelVersion.model_id == model_id
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def exists(self, model_id: int, version: str) -> bool:
        stmt = select(ModelVersion.id).where(
            ModelVersion.model_id == model_id, ModelVersion.version == version
        )
        return (await self.session.execute(stmt)).first() is not None

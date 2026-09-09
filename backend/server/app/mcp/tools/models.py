"""Model-registry tools — models and their versions."""

from __future__ import annotations

from dqh.svc_core.transports.http import PaginationParams

from app.mcp._session import session_scope
from app.modules.model_registry import ModelRegistryService
from app.modules.model_registry.rules import ModelTask


async def list_models(task: str | None = None, limit: int = 50) -> dict:
    """List registered models, optionally by task (detection|classification|...)."""
    t = ModelTask(task) if task else None
    async with session_scope() as session:
        page = await ModelRegistryService(session).list_models(
            task=t, params=PaginationParams(page=1, page_size=min(limit, 200))
        )
        return {
            "total": page.total,
            "models": [
                {"id": m.id, "name": m.name, "task": str(m.task), "architecture": m.architecture}
                for m in page.items
            ],
        }


async def get_model(model_id: int) -> dict:
    """A model and all its versions (status, format, image digests, metrics)."""
    async with session_scope() as session:
        m = await ModelRegistryService(session).get_model(model_id)
        return {
            "id": m.id,
            "name": m.name,
            "task": str(m.task),
            "architecture": m.architecture,
            "versions": [
                {
                    "id": v.id,
                    "version": v.version,
                    "status": str(v.status),
                    "format": str(v.format),
                    "image_repo": v.image_repo,
                    "image_cpu_digest": v.image_cpu_digest,
                    "image_gpu_digest": v.image_gpu_digest,
                    "metrics": v.metrics,
                }
                for v in m.versions
            ],
        }


TOOLS = [list_models, get_model]

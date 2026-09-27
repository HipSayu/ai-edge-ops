"""Model-catalog tools — model images read live from the OCI registry."""

from __future__ import annotations

from app.core.model_catalog import model_catalog


async def list_models(limit: int = 50) -> dict:
    """List available model images (tag, digest, task, classes, metrics)."""
    images = await model_catalog.list_models()
    return {
        "total": len(images),
        "models": [m.model_dump(mode="json") for m in images[:limit]],
    }


async def get_model(tag: str) -> dict:
    """One model image by tag — labels, platforms, digest-pinned ref."""
    return (await model_catalog.get_model(tag)).model_dump(mode="json")


TOOLS = [list_models, get_model]

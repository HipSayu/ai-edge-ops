"""ModelCatalog reads tags + labels from a (mocked) OCI Registry v2 API."""

from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import ModelRegistryConfig
from app.modules.model_registry.catalog import ModelCatalog

_CONFIG_DIGEST = "sha256:cfg"
_MANIFEST_DIGEST = "sha256:idx"

_CONFIG_BLOB = {
    "created": "2026-09-01T10:00:00Z",
    "config": {
        "Labels": {
            "org.opencontainers.image.version": "1.3.0",
            "ai.edge-ops.model.task": "detect",
            "ai.edge-ops.model.classes": "helmet, vest, person",
            "ai.edge-ops.model.map50_95": "0.41",
            "ai.edge-ops.model.params_m": "2.6",
        }
    },
}

_INDEX = {
    "manifests": [
        {"digest": "sha256:amd", "platform": {"os": "linux", "architecture": "amd64"}},
        {"digest": "sha256:arm", "platform": {"os": "linux", "architecture": "arm64"}},
    ]
}

_IMAGE_MANIFEST = {
    "config": {"digest": _CONFIG_DIGEST},
    "layers": [{"size": 1000}, {"size": 2000}],
}


def _handler(request: httpx.Request) -> httpx.Response:
    p = request.url.path
    if p == "/token":
        return httpx.Response(200, json={"token": "anon"})
    if p == "/v2/acme/ppe/tags/list":
        return httpx.Response(200, json={"tags": ["1.3.0", "latest"]})
    if p == "/v2/acme/ppe/manifests/1.3.0":
        return httpx.Response(
            200, json=_INDEX, headers={"docker-content-digest": _MANIFEST_DIGEST}
        )
    if p == "/v2/acme/ppe/manifests/sha256:amd":
        return httpx.Response(200, json=_IMAGE_MANIFEST)
    if p == f"/v2/acme/ppe/blobs/{_CONFIG_DIGEST}":
        return httpx.Response(200, content=json.dumps(_CONFIG_BLOB))
    return httpx.Response(404)


@pytest.fixture
def catalog() -> ModelCatalog:
    cfg = ModelRegistryConfig(owner="acme", package="ppe", ttl_s=0)
    return ModelCatalog(cfg, transport=httpx.MockTransport(_handler))


async def test_list_models_parses_labels(catalog: ModelCatalog):
    models = await catalog.list_models()

    assert len(models) == 1
    m = models[0]
    assert m.tag == "1.3.0"
    assert m.ref == "ghcr.io/acme/ppe:1.3.0"
    assert m.digest == _MANIFEST_DIGEST
    assert m.task == "detect"
    assert m.classes == ["helmet", "vest", "person"]
    assert m.map50_95 == 0.41
    assert m.params_m == 2.6
    assert m.platforms == ["linux/amd64", "linux/arm64"]
    assert m.size_bytes == 3000
    assert m.created_at is not None and m.created_at.year == 2026


async def test_latest_tag_is_hidden(catalog: ModelCatalog):
    assert [m.tag for m in await catalog.list_models()] == ["1.3.0"]


async def test_unconfigured_catalog_is_empty():
    empty = ModelCatalog(ModelRegistryConfig())
    assert await empty.list_models() == []


async def test_get_model_404_raises_not_found(catalog: ModelCatalog):
    from dqh.svc_core.contracts.errors import NotFoundError

    with pytest.raises(NotFoundError):
        await catalog.get_model("nope")

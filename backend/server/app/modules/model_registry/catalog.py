"""Read the model catalog straight from an OCI registry (GHCR) — no DB.

Each model version is one multi-arch image tag. Metadata lives in the image
config labels (``ai.edge-ops.model.*`` + ``org.opencontainers.image.*``), baked
by the model pipeline. The package is public, so every call goes through the
anonymous Registry v2 token flow; ``ModelRegistryConfig.token`` is only needed
for a private package or to lift the GHCR rate limit.
"""

from __future__ import annotations

import asyncio
import base64
import datetime as dt
import time

import httpx
from pydantic import BaseModel, Field

from app.core.config import ModelRegistryConfig

_MANIFEST_ACCEPT = ", ".join(
    (
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    )
)


class ModelImage(BaseModel):
    """One model version = one image tag. Shape the frontend / deploy consume."""

    name: str  # package name
    tag: str
    ref: str  # host/owner/package:tag
    digest: str  # manifest (list) digest, sha256:...
    created_at: dt.datetime | None = None
    platforms: list[str] = Field(default_factory=list)
    size_bytes: int = 0
    # from labels
    task: str | None = None
    classes: list[str] = Field(default_factory=list)
    map50_95: float | None = None
    params_m: float | None = None
    latency_ms: float | None = None
    base: str | None = None


class ModelCatalog:
    def __init__(self, config: ModelRegistryConfig, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._cfg = config
        self._transport = transport  # tests inject httpx.MockTransport
        self._cache: dict[str, tuple[float, ModelImage]] = {}
        self._tags_cache: tuple[float, list[str]] | None = None
        self._bearer: str | None = None
        self._lock = asyncio.Lock()

    # --- public ------------------------------------------------------------
    async def list_models(self, *, refresh: bool = False) -> list[ModelImage]:
        tags = await self._tags(refresh=refresh)
        out = await asyncio.gather(
            *(self._image(tag, refresh=refresh) for tag in tags), return_exceptions=True
        )
        images = [img for img in out if isinstance(img, ModelImage)]
        images.sort(key=lambda i: (i.created_at or dt.datetime.min), reverse=True)
        return images

    async def get_model(self, tag: str, *, refresh: bool = False) -> ModelImage:
        return await self._image(tag, refresh=refresh)

    # --- registry v2 -----------------------------------------------------
    async def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=f"https://{self._cfg.host}", timeout=15.0, transport=self._transport
        )

    async def _token(self, client: httpx.AsyncClient) -> str:
        if self._bearer:
            return self._bearer
        headers = {}
        if self._cfg.token:
            basic = base64.b64encode(f"x:{self._cfg.token}".encode()).decode()
            headers["Authorization"] = f"Basic {basic}"
        r = await client.get(
            "/token",
            params={"service": self._cfg.host, "scope": f"repository:{self._cfg.repo}:pull"},
            headers=headers,
        )
        r.raise_for_status()
        self._bearer = r.json().get("token") or r.json().get("access_token", "")
        return self._bearer

    async def _get(self, client: httpx.AsyncClient, path: str, *, accept: str | None = None):
        headers = {"Authorization": f"Bearer {await self._token(client)}"}
        if accept:
            headers["Accept"] = accept
        r = await client.get(f"/v2/{self._cfg.repo}{path}", headers=headers)
        r.raise_for_status()
        return r

    async def _tags(self, *, refresh: bool) -> list[str]:
        if not self._cfg.configured:
            return []
        now = time.monotonic()
        if not refresh and self._tags_cache and now < self._tags_cache[0]:
            return self._tags_cache[1]
        async with await self._client() as client:
            r = await self._get(client, "/tags/list")
        tags = [t for t in r.json().get("tags", []) if t != "latest"]
        self._tags_cache = (now + self._cfg.ttl_s, tags)
        return tags

    async def _image(self, tag: str, *, refresh: bool) -> ModelImage:
        now = time.monotonic()
        if not refresh and (hit := self._cache.get(tag)) and now < hit[0]:
            return hit[1]
        async with await self._client() as client:
            top = await self._get(client, f"/manifests/{tag}", accept=_MANIFEST_ACCEPT)
            top_digest = top.headers.get("docker-content-digest", "")
            doc = top.json()

            platforms: list[str] = []
            if "manifests" in doc:  # index / manifest list
                for m in doc["manifests"]:
                    p = m.get("platform", {})
                    if p.get("os") and p.get("architecture"):
                        platforms.append(f"{p['os']}/{p['architecture']}")
                child = doc["manifests"][0]["digest"]
                img = (await self._get(client, f"/manifests/{child}", accept=_MANIFEST_ACCEPT)).json()
            else:
                img = doc

            size = sum(int(layer.get("size", 0)) for layer in img.get("layers", []))
            cfg = await self._get(client, f"/blobs/{img['config']['digest']}")
        blob = cfg.json()
        labels = (blob.get("config", {}) or {}).get("Labels") or {}

        image = ModelImage(
            name=self._cfg.package,
            tag=tag,
            ref=f"{self._cfg.host}/{self._cfg.repo}:{tag}",
            digest=top_digest or img.get("config", {}).get("digest", ""),
            created_at=_parse_dt(labels.get("org.opencontainers.image.created") or blob.get("created")),
            platforms=platforms,
            size_bytes=size,
            task=labels.get("ai.edge-ops.model.task"),
            classes=_split(labels.get("ai.edge-ops.model.classes")),
            map50_95=_num(labels.get("ai.edge-ops.model.map50_95")),
            params_m=_num(labels.get("ai.edge-ops.model.params_m")),
            latency_ms=_num(labels.get("ai.edge-ops.model.latency_ms")),
            base=labels.get("ai.edge-ops.model.base"),
        )
        self._cache[tag] = (now + self._cfg.ttl_s, image)
        return image


def _parse_dt(raw: str | None) -> dt.datetime | None:
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _split(raw: str | None) -> list[str]:
    return [p.strip() for p in raw.split(",") if p.strip()] if raw else []


def _num(raw: str | None) -> float | None:
    try:
        return float(raw) if raw not in (None, "") else None
    except (TypeError, ValueError):
        return None


__all__ = ["ModelCatalog", "ModelImage"]

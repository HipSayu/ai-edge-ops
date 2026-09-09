"""Model registry API contract — one model version = one OCI image tag."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field, computed_field


class ModelImage(BaseModel):
    """What the frontend lists and the deploy flow resolves against."""

    name: str  # package name
    tag: str
    ref: str  # host/owner/package:tag
    digest: str  # manifest (list) digest, sha256:...
    created_at: dt.datetime | None = None
    platforms: list[str] = Field(default_factory=list)
    size_bytes: int = 0

    # from the ai.edge-ops.model.* image labels
    task: str | None = None
    classes: list[str] = Field(default_factory=list)
    map50_95: float | None = None
    params_m: float | None = None
    latency_ms: float | None = None
    base: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pinned_ref(self) -> str:
        """Digest-pinned ref for an immutable pull on the edge."""
        stem = self.ref.rsplit(":", 1)[0]
        return f"{stem}@{self.digest}" if self.digest else self.ref


__all__ = ["ModelImage"]

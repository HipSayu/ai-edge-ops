from typing import Any

from pydantic import BaseModel


class DeploymentUpdate(BaseModel):
    image_uri: str | None = None
    image_tag: str | None = None
    model_id: str | None = None
    model_uri: str | None = None
    config: dict[str, Any] | None = None
    environment: dict[str, str] | None = None
    resource_limits: dict[str, Any] | None = None

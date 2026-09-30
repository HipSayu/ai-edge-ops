from typing import Any

from pydantic import BaseModel, Field

from src.shared.contracts import RuntimeType


class DeploymentRequest(BaseModel):
    node_id: str
    name: str = Field(min_length=1, max_length=255)
    type: RuntimeType = RuntimeType.VISION
    image_uri: str
    image_tag: str = "latest"
    model_id: str | None = None
    model_uri: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, str] = Field(default_factory=dict)
    resource_limits: dict[str, Any] = Field(default_factory=dict)

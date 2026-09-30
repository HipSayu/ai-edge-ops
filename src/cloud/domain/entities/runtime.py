from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.shared.contracts import RuntimeStatus, RuntimeType


@dataclass(slots=True)
class Runtime:
    id: str
    node_id: str
    name: str
    type: RuntimeType = RuntimeType.VISION
    status: RuntimeStatus = RuntimeStatus.UNKNOWN
    image_uri: str | None = None
    image_tag: str | None = None
    model_id: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    resource_limits: dict[str, Any] = field(default_factory=dict)
    container_id: str | None = None
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

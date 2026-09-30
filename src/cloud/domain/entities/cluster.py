from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.shared.contracts import ClusterStatus


@dataclass(slots=True)
class Cluster:
    id: str
    name: str
    description: str | None = None
    status: ClusterStatus = ClusterStatus.UNKNOWN
    location: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

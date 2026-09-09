"""Events published by the deployment module."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeploymentActivated:
    deployment_id: int
    device_id: int
    image: str
    config: dict[str, Any]


@dataclass(frozen=True)
class DeploymentFailed:
    deployment_id: int
    device_id: int
    reason: str
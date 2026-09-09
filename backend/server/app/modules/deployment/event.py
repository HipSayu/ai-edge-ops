"""Events for the deployment flow - there is no deployment table."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DeployRequested:
    """The operator set a device's desired model image - send the command."""

    device_id: str
    image: str  # digest-pinned OCI ref
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentFailed:
    device_id: str
    reason: str
    deployment_id: int | None = None


@dataclass(frozen=True)
class ConfigResolved:
    """A device's effective inference config changed - push T_UPDATE_CONFIG."""

    device_id: str
    config: dict[str, Any] = field(default_factory=dict)

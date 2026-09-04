"""Deployment domain: status model, events, transition rules."""

from __future__ import annotations

from dataclasses import dataclass

from app.shared.enum import StrEnum


class DeploymentStatus(StrEnum):
    PENDING = "pending"  # created, not yet rolled out to the device
    ACTIVE = "active"  # currently serving on the device
    FAILED = "failed"  # rollout failed
    ROLLED_BACK = "rolled_back"
    SUPERSEDED = "superseded"  # replaced by a newer deployment on the same device


ACTIVE_STATUSES = frozenset({DeploymentStatus.ACTIVE})

_FLOW: dict[DeploymentStatus, set[DeploymentStatus]] = {
    DeploymentStatus.PENDING: {DeploymentStatus.ACTIVE, DeploymentStatus.FAILED},
    DeploymentStatus.ACTIVE: {DeploymentStatus.ROLLED_BACK, DeploymentStatus.SUPERSEDED},
    DeploymentStatus.FAILED: {DeploymentStatus.PENDING},
    DeploymentStatus.ROLLED_BACK: set(),
    DeploymentStatus.SUPERSEDED: set(),
}


def can_transition(current: DeploymentStatus, target: DeploymentStatus) -> bool:
    return target in _FLOW[current]


@dataclass(frozen=True)
class DeploymentActivated:
    deployment_id: int
    device_id: int
    model_version_id: int


@dataclass(frozen=True)
class DeploymentFailed:
    deployment_id: int
    device_id: int
    reason: str

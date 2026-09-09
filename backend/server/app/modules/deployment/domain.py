"""Deployment status model and transition rules."""

from dqh.svc_core.helpers.str_enum import StrEnum


class DeploymentStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SUPERSEDED = "superseded"


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
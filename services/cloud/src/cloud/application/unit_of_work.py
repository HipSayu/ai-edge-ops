"""One transaction over the whole service. It spans both contexts (identity and PPE), so the port lives here,
above them, and each context's services take it as a plain callable."""

from collections.abc import Callable
from typing import Protocol

from cloud.application.ports import CameraReader
from cloud.domain.repositories import (
    ClusterRepository, NodeRepository, UserRepository, ViolationEventRepository, ZoneRepository,
)


class UnitOfWork(Protocol):
    """One transaction. Leaving the block commits it, unless an exception is leaving, which rolls it back."""

    clusters: ClusterRepository
    nodes: NodeRepository
    users: UserRepository
    events: ViolationEventRepository
    cameras: CameraReader
    zones: ZoneRepository

    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type, exc, tb) -> None: ...


UnitOfWorkFactory = Callable[[], UnitOfWork]

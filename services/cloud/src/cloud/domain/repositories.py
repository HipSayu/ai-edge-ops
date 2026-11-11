"""Repository interfaces for the aggregates (users, clusters, nodes, violation events). Implemented in infrastructure; each hands out domain objects only."""

from collections.abc import Collection
from datetime import datetime
from typing import Protocol

from cloud.domain.model.cluster import Cluster
from cloud.domain.model.node import Node
from cloud.domain.model.user import User
from cloud.domain.violation.violation_event import ViolationEvent
from cloud.domain.model.zone import Zone


class ClusterRepository(Protocol):
    def get(self, cluster_id: int) -> Cluster | None: ...

    def by_name(self, name: str) -> Cluster | None: ...

    def list(self) -> list[Cluster]: ...

    def add(self, cluster: Cluster) -> Cluster: ...

    def save(self, cluster: Cluster) -> None: ...

    def remove(self, cluster_id: int) -> None:
        """Also removes the nodes and cameras inside."""


class NodeRepository(Protocol):
    def get(self, node_id: int) -> Node | None: ...

    def get_by_camera(self, camera_id: int) -> Node | None: ...

    def list(self, cluster_id: int | None = None) -> list[Node]: ...

    def add(self, node: Node) -> Node:
        """Assigns ids to the node and its new cameras."""

    def save(self, node: Node) -> None:
        """Stores the node and its cameras; cameras gone from the node are deleted, new ones get ids."""

    def remove(self, node_id: int) -> None: ...


class ViolationEventRepository(Protocol):
    def add(self, event: ViolationEvent) -> ViolationEvent: ...

    def get(self, event_id: int) -> ViolationEvent | None: ...

    def recent(
        self, camera_ids: Collection[int], since: datetime | None = None,
        violation_type: str | None = None, limit: int = 10,
    ) -> list[ViolationEvent]:
        """Newest first."""

    def between(self, camera_ids: Collection[int], start: datetime, end: datetime | None = None) -> list[ViolationEvent]: ...

    def counts_by_type(
        self, camera_ids: Collection[int], since: datetime, violation_type: str | None = None
    ) -> dict[str, int]: ...

    def counts_by_camera(
        self, camera_ids: Collection[int], since: datetime, violation_type: str | None = None
    ) -> dict[int, int]: ...


class UserRepository(Protocol):
    def get(self, user_id: int) -> User | None: ...

    def by_username(self, username: str) -> User | None: ...

    def list(self) -> list[User]: ...

    def add(self, user: User) -> User: ...

    def save(self, user: User) -> None: ...

    def remove(self, user_id: int) -> None: ...


class ZoneRepository(Protocol):
    def for_camera(self, camera_id: int) -> list[Zone]: ...

    def replace(self, camera_id: int, zones: list[Zone]) -> list[Zone]:
        """Makes `zones` the camera's zones (the ones it had are gone) and returns them with their ids."""

"""SQLAlchemy implementations of the PPE repositories and the camera read side."""

import json
from collections.abc import Collection
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from cloud.application.dto.read_models import CameraRow
from cloud.domain.model.cluster import Cluster
from cloud.domain.model.node import Node
from cloud.domain.violation.violation_event import ViolationEvent
from cloud.domain.model.zone import Zone
from cloud.domain.model.user import User
from cloud.infrastructure.persistence.mappers import to_cluster, to_event, to_node, to_user
from cloud.infrastructure.persistence.models import (
    CameraRecord,
    ClusterRecord,
    NodeRecord,
    UserRecord,
    ViolationEventRecord,
    ZoneRecord,
)
from shared.errors import NotAllowed
from shared.roles import Role


class SqlClusterRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, cluster_id: int) -> Cluster | None:
        record = self._session.get(ClusterRecord, cluster_id)
        return to_cluster(record) if record else None

    def by_name(self, name: str) -> Cluster | None:
        record = self._session.scalar(select(ClusterRecord).where(ClusterRecord.name == name))
        return to_cluster(record) if record else None

    def list(self) -> list[Cluster]:
        return [to_cluster(r) for r in self._session.scalars(select(ClusterRecord).order_by(ClusterRecord.id))]

    def add(self, cluster: Cluster) -> Cluster:
        record = ClusterRecord(name=cluster.name, description=cluster.description)
        self._session.add(record)
        self._session.flush()  # the id is needed by the caller
        cluster.id = record.id
        return cluster

    def save(self, cluster: Cluster) -> None:
        record = self._session.get(ClusterRecord, cluster.id)
        record.name, record.description = cluster.name, cluster.description
        self._session.flush()

    def remove(self, cluster_id: int) -> None:
        record = self._session.get(ClusterRecord, cluster_id)
        if record is not None:
            self._session.delete(record)  # nodes and cameras follow through the cascade
            self._session.flush()


class SqlNodeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, node_id: int) -> Node | None:
        record = self._session.get(NodeRecord, node_id)
        return to_node(record) if record else None

    def get_by_camera(self, camera_id: int) -> Node | None:
        record = self._session.scalar(
            select(NodeRecord).join(CameraRecord, CameraRecord.node_id == NodeRecord.id).where(CameraRecord.id == camera_id)
        )
        return to_node(record) if record else None

    def list(self, cluster_id: int | None = None) -> list[Node]:
        query = select(NodeRecord).order_by(NodeRecord.id)
        if cluster_id is not None:
            query = query.where(NodeRecord.cluster_id == cluster_id)
        return [to_node(r) for r in self._session.scalars(query)]

    def add(self, node: Node) -> Node:
        record = NodeRecord(
            cluster_id=node.cluster_id, name=node.name, max_cameras=node.max_cameras,
            description=node.description, ip_address=node.ip_address,
        )
        self._session.add(record)
        self._session.flush()
        node.id = record.id
        self.save(node)  # stores the cameras the node already holds
        return node

    def save(self, node: Node) -> None:
        record = self._session.get(NodeRecord, node.id)
        if record is None:
            raise NotAllowed(f"Không tìm thấy node {node.id}")
        record.cluster_id, record.name, record.max_cameras = node.cluster_id, node.name, node.max_cameras
        record.description, record.ip_address = node.description, node.ip_address

        existing = {c.id: c for c in record.cameras}
        new: list[tuple] = []
        for camera in node.cameras:
            if camera.id is None:
                row = CameraRecord(name=camera.name, zone=camera.zone, enabled=camera.enabled)
                record.cameras.append(row)
                new.append((camera, row))
            else:
                row = existing[camera.id]
                row.name, row.zone, row.enabled = camera.name, camera.zone, camera.enabled
        kept = {c.id for c in node.cameras if c.id is not None}
        for camera_id, row in existing.items():
            if camera_id not in kept:
                record.cameras.remove(row)  # delete-orphan removes it
        self._session.flush()
        for camera, row in new:
            camera.id = row.id

    def remove(self, node_id: int) -> None:
        record = self._session.get(NodeRecord, node_id)
        if record is not None:
            self._session.delete(record)
            self._session.flush()


class SqlViolationEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, event: ViolationEvent) -> ViolationEvent:
        record = ViolationEventRecord(
            camera_id=event.camera_id, violation_type=event.violation_type, confidence=event.confidence,
            video_ts_sec=event.video_ts_sec, snapshot_path=event.snapshot_path, created_at=event.created_at,
        )
        self._session.add(record)
        self._session.flush()
        event.id = record.id
        return event

    def get(self, event_id: int) -> ViolationEvent | None:
        record = self._session.get(ViolationEventRecord, event_id)
        return to_event(record) if record else None

    def recent(
        self, camera_ids: Collection[int], since: datetime | None = None,
        violation_type: str | None = None, limit: int = 10,
    ) -> list[ViolationEvent]:
        if not camera_ids or limit <= 0:
            return []
        query = select(ViolationEventRecord).where(ViolationEventRecord.camera_id.in_(camera_ids))
        if since is not None:
            query = query.where(ViolationEventRecord.created_at >= since)
        if violation_type:
            query = query.where(ViolationEventRecord.violation_type == violation_type)
        query = query.order_by(ViolationEventRecord.created_at.desc()).limit(limit)
        return [to_event(r) for r in self._session.scalars(query)]

    def between(self, camera_ids: Collection[int], start: datetime, end: datetime | None = None) -> list[ViolationEvent]:
        if not camera_ids:
            return []
        query = select(ViolationEventRecord).where(
            ViolationEventRecord.camera_id.in_(camera_ids), ViolationEventRecord.created_at >= start
        )
        if end is not None:
            query = query.where(ViolationEventRecord.created_at < end)
        return [to_event(r) for r in self._session.scalars(query)]

    def counts_by_type(
        self, camera_ids: Collection[int], since: datetime, violation_type: str | None = None
    ) -> dict[str, int]:
        return dict(self._counts(ViolationEventRecord.violation_type, camera_ids, since, violation_type))

    def counts_by_camera(
        self, camera_ids: Collection[int], since: datetime, violation_type: str | None = None
    ) -> dict[int, int]:
        return dict(self._counts(ViolationEventRecord.camera_id, camera_ids, since, violation_type))

    def _counts(self, column, camera_ids: Collection[int], since: datetime, violation_type: str | None):
        if not camera_ids:
            return []
        query = (
            select(column, func.count())
            .where(ViolationEventRecord.created_at >= since, ViolationEventRecord.camera_id.in_(camera_ids))
            .group_by(column)
        )
        if violation_type:
            query = query.where(ViolationEventRecord.violation_type == violation_type)
        return self._session.execute(query).all()


class SqlCameraReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def rows(self) -> list[CameraRow]:
        rows = self._session.execute(
            select(
                CameraRecord.id, CameraRecord.name, CameraRecord.zone, CameraRecord.enabled,
                NodeRecord.id, NodeRecord.name, ClusterRecord.id, ClusterRecord.name,
            )
            .join(NodeRecord, CameraRecord.node_id == NodeRecord.id)
            .join(ClusterRecord, NodeRecord.cluster_id == ClusterRecord.id)
            .order_by(CameraRecord.id)
        ).all()
        return [CameraRow(*row) for row in rows]


class SqlZoneRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def for_camera(self, camera_id: int) -> list[Zone]:
        records = self._session.scalars(select(ZoneRecord).where(ZoneRecord.camera_id == camera_id).order_by(ZoneRecord.id))
        return [_to_zone(r) for r in records]

    def replace(self, camera_id: int, zones: list[Zone]) -> list[Zone]:
        self._session.execute(delete(ZoneRecord).where(ZoneRecord.camera_id == camera_id))
        records = [
            ZoneRecord(camera_id=camera_id, name=z.name, polygon=json.dumps([list(c) for c in z.polygon]), enabled=z.enabled)
            for z in zones
        ]
        self._session.add_all(records)
        self._session.flush()
        return [_to_zone(r) for r in records]


def _to_zone(record: ZoneRecord) -> Zone:
    return Zone(
        name=record.name, polygon=tuple((float(x), float(y)) for x, y in json.loads(record.polygon)),
        enabled=record.enabled, id=record.id,
    )


class SqlUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: int) -> User | None:
        record = self._session.get(UserRecord, user_id)
        return to_user(record) if record else None

    def by_username(self, username: str) -> User | None:
        record = self._session.scalar(select(UserRecord).where(UserRecord.username == username))
        return to_user(record) if record else None

    def list(self) -> list[User]:
        return [to_user(r) for r in self._session.scalars(select(UserRecord).order_by(UserRecord.id))]

    def add(self, user: User) -> User:
        record = UserRecord(username=user.username, password_hash=user.password_hash)
        self._copy(user, record)
        self._session.add(record)
        self._session.flush()
        user.id = record.id
        return user

    def save(self, user: User) -> None:
        record = self._session.get(UserRecord, user.id)
        record.password_hash = user.password_hash
        self._copy(user, record)
        self._session.flush()

    def remove(self, user_id: int) -> None:
        record = self._session.get(UserRecord, user_id)
        if record is not None:
            self._session.delete(record)
            self._session.flush()

    def _copy(self, user: User, record: UserRecord) -> None:
        record.full_name, record.role, record.is_active = user.full_name, Role(user.role).value, user.is_active
        record.clusters = (
            list(self._session.scalars(select(ClusterRecord).where(ClusterRecord.id.in_(user.cluster_ids))))
            if user.cluster_ids
            else []
        )

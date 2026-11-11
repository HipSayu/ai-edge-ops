"""Rows to domain objects. Repositories use these so nothing outside persistence sees a row."""

from datetime import UTC, datetime

from cloud.domain.model.cluster import Cluster
from cloud.domain.model.node import Camera, Node
from cloud.domain.model.user import User
from cloud.domain.violation.violation_event import ViolationEvent
from cloud.infrastructure.persistence.models import (
    CameraRecord,
    ClusterRecord,
    NodeRecord,
    UserRecord,
    ViolationEventRecord,
)
from shared.roles import Role


def _aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)  # SQLite drops the zone


def to_cluster(record: ClusterRecord) -> Cluster:
    return Cluster(id=record.id, name=record.name, description=record.description)


def to_camera(record: CameraRecord) -> Camera:
    return Camera(id=record.id, name=record.name, zone=record.zone, enabled=record.enabled)


def to_node(record: NodeRecord) -> Node:
    return Node(
        id=record.id, cluster_id=record.cluster_id, name=record.name, max_cameras=record.max_cameras,
        description=record.description, ip_address=record.ip_address,
        cameras=[to_camera(c) for c in record.cameras],
    )


def to_user(record: UserRecord) -> User:
    return User(
        id=record.id, username=record.username, password_hash=record.password_hash, full_name=record.full_name,
        role=Role(record.role), is_active=record.is_active, cluster_ids=[c.id for c in record.clusters],
    )


def to_event(record: ViolationEventRecord) -> ViolationEvent:
    return ViolationEvent(
        id=record.id, camera_id=record.camera_id, violation_type=record.violation_type,
        confidence=record.confidence, video_ts_sec=record.video_ts_sec,
        snapshot_path=record.snapshot_path, created_at=_aware(record.created_at),
    )

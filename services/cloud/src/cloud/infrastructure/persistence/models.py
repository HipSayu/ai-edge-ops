"""Database tables of the cloud service. Storage rows only: repositories map them to and from domain objects."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# AUTOINCREMENT on SQLite: a deleted id is never reused, so video folders named by id never get mixed up
_STABLE_IDS = {"sqlite_autoincrement": True}


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


user_clusters = Table(
    "user_clusters",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("cluster_id", ForeignKey("clusters.id", ondelete="CASCADE"), primary_key=True),
)


class ClusterRecord(Base):
    __tablename__ = "clusters"
    __table_args__ = _STABLE_IDS

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    nodes: Mapped[list["NodeRecord"]] = relationship(
        back_populates="cluster", cascade="all, delete-orphan", order_by="NodeRecord.id"
    )


class NodeRecord(Base):
    __tablename__ = "nodes"
    __table_args__ = _STABLE_IDS

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    max_cameras: Mapped[int] = mapped_column(Integer, default=16)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cluster: Mapped[ClusterRecord] = relationship(back_populates="nodes")
    cameras: Mapped[list["CameraRecord"]] = relationship(
        back_populates="node", cascade="all, delete-orphan", order_by="CameraRecord.id"
    )


class CameraRecord(Base):
    __tablename__ = "cameras"
    __table_args__ = _STABLE_IDS

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    zone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    node: Mapped[NodeRecord] = relationship(back_populates="cameras")


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    clusters: Mapped[list[ClusterRecord]] = relationship(secondary=user_clusters, lazy="selectin")


class ViolationEventRecord(Base):
    __tablename__ = "violation_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), index=True)
    violation_type: Mapped[str] = mapped_column(String(40), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    video_ts_sec: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    snapshot_path: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ZoneRecord(Base):
    """A forbidden zone of a camera. The corners are a JSON list of [x, y] fractions of the picture."""

    __tablename__ = "camera_zones"
    __table_args__ = _STABLE_IDS

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    polygon: Mapped[str] = mapped_column(String(4000))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

"""Agent ORM: Device - the *desired* config of an edge box (operator-owned).

The *reported* half (online, health, running image, probed hardware) is not
here - it lives in the in-memory :class:`app.modules.agent.fleet_registry.FleetRegistry`,
rebuilt from MQTT on every server start.
"""

from __future__ import annotations

from dqh.svc_core.persistence.sqlalchemy import TimestampMixin
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    # the string DEVICE_ID the box is provisioned with (also the MQTT identity)
    device_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    site: Mapped[str] = mapped_column(String(128), index=True)
    labels: Mapped[dict] = mapped_column(JSON, default=dict)

    # desired state pushed to the device
    desired_image: Mapped[str | None] = mapped_column(String(512), default=None)
    cameras: Mapped[list] = mapped_column(JSON, default=list)
    inference: Mapped[dict] = mapped_column(JSON, default=dict)   # sparse threshold overrides
    agent_config: Mapped[dict] = mapped_column(JSON, default=dict)  # log level, intervals

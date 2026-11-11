"""Demo accounts, one cluster and one node, created only when the users table is empty."""

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from cloud.infrastructure.persistence.models import ClusterRecord, NodeRecord, UserRecord
from cloud.infrastructure.security.passwords import hash_password
from shared.roles import Role


def seed_if_empty(session_factory: sessionmaker) -> None:
    with session_factory() as session:
        if session.scalar(select(func.count()).select_from(UserRecord)):
            return

        site = ClusterRecord(name="Công trường mẫu", description="Dữ liệu demo")
        site.nodes.append(NodeRecord(name="Node local", max_cameras=16))
        session.add(site)
        session.flush()

        session.add_all(
            [
                UserRecord(username="admin", password_hash=hash_password("admin123"),
                           full_name="Quản trị viên", role=Role.ADMIN.value, is_active=True),
                UserRecord(username="operator1", password_hash=hash_password("demo123"),
                           full_name="Nguyễn Văn Vận", role=Role.OPERATOR.value, is_active=True, clusters=[site]),
                UserRecord(username="viewer1", password_hash=hash_password("demo123"),
                           full_name="Trần Thị Xem", role=Role.VIEWER.value, is_active=True, clusters=[site]),
            ]
        )
        session.commit()

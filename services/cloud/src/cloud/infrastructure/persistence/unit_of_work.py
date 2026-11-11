from sqlalchemy.orm import Session, sessionmaker

from cloud.infrastructure.persistence.repositories import (
    SqlCameraReader,
    SqlClusterRepository,
    SqlNodeRepository,
    SqlViolationEventRepository,
    SqlZoneRepository,
)
from cloud.infrastructure.persistence.repositories import SqlUserRepository


class SqlAlchemyUnitOfWork:
    """One database transaction. Leaving the block commits it; an exception rolls it back."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._factory()
        self.clusters = SqlClusterRepository(self._session)
        self.nodes = SqlNodeRepository(self._session)
        self.users = SqlUserRepository(self._session)
        self.events = SqlViolationEventRepository(self._session)
        self.cameras = SqlCameraReader(self._session)
        self.zones = SqlZoneRepository(self._session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self._session.commit()
            else:
                self._session.rollback()
        finally:
            self._session.close()

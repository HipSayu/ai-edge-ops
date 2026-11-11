from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from cloud.infrastructure.persistence.models import Base


def create_engine_for(url: str) -> Engine:
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})

    if url.startswith("sqlite"):
        # SQLite ignores foreign keys unless asked; cascades depend on this
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)


def create_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)

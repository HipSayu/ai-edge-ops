from pydantic_settings import BaseSettings


class PostgresSettings(BaseSettings):
    database_url: str = "postgresql://edgeops:edgeops@localhost:5432/edgeops"

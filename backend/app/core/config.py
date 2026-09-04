"""App-wide settings, loaded from environment variables (.env)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    environment: str = "local"
    app_name: str = "AI Edge Ops API"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://ppe:ppe@localhost:5432/ai_edge_ops"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Fleet health evaluation
    offline_threshold_seconds: int = 90
    latency_slo_ms: float = 80.0

    @property
    def is_local(self) -> bool:
        return self.environment == "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

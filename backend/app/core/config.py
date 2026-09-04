"""The single settings object for the backend.

One :class:`Settings` instance, nested connection groups from
``dqh.svc_core.config``. Env vars use ``__`` to descend:

    DB__URL, DB__POOL_SIZE
    MQTT__HOST, MQTT__PORT, MQTT__TLS
    S3__ENDPOINT_URL, S3__BUCKET
    REDIS__URL

Top-level values (ENVIRONMENT, CORS_ORIGINS, ...) have no prefix.
"""

from __future__ import annotations

from functools import lru_cache

from dqh.svc_core.config import (
    BaseAppSettings,
    DatabaseConfig,
    MqttConfig,
    RedisConfig,
    S3Config,
)
from pydantic import Field


class Settings(BaseAppSettings):
    service_name: str = "ai-edge-ops"
    app_name: str = "AI Edge Ops API"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Fleet health evaluation
    offline_threshold_seconds: int = 90
    latency_slo_ms: float = 80.0

    # Edge transport: "memory" (in-process) or "mqtt"
    edge_transport: str = "memory"

    # --- backing services (env: DB__* / MQTT__* / REDIS__* / S3__*) ------
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    s3: S3Config = Field(default_factory=S3Config)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

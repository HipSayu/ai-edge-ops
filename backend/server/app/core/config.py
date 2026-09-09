"""The single settings object for the backend.

One :class:`Settings` instance, nested connection groups from
``dqh.svc_core.config``. Env vars use ``__`` to descend:

    DB__URL, DB__POOL_SIZE
    MQTT__HOST, MQTT__PORT, MQTT__TLS
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
)
from pydantic import BaseModel, Field


class ModelRegistryConfig(BaseModel):
    """Model catalog source — an OCI registry. env: ``MODEL_REGISTRY__*``.

    The model package is public (built by a separate pipeline), so ``token`` is
    optional — only for a private package or to lift the GHCR rate limit.
    """

    host: str = "ghcr.io"
    owner: str = ""
    package: str = ""
    token: str | None = None
    ttl_s: float = 30.0

    @property
    def repo(self) -> str:
        return f"{self.owner}/{self.package}"

    @property
    def configured(self) -> bool:
        return bool(self.owner and self.package)


class Settings(BaseAppSettings):
    service_name: str = "ai-edge-ops"
    app_name: str = "AI Edge Ops API"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Agent health evaluation
    offline_threshold_seconds: int = 90
    latency_slo_ms: float = 80.0
    evidence_dir: str = "var/evidence"
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30

    # Edge transport: "memory" (in-process) or "mqtt"
    edge_transport: str = "memory"
    # Browser realtime fan-out: "memory" (single replica) or "redis" (multi-replica)
    realtime_transport: str = "memory"

    # WebRTC video streaming (edge -> MediaMTX -> frontend), see app/modules/streaming
    mediamtx_whip_url: str = "http://localhost:8889"
    mediamtx_whep_url: str = "http://localhost:8889"
    stream_token_seconds: int = 30

    # --- backing services (env: DB__* / MQTT__* / REDIS__*) ----------------
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # --- model catalog, read live from an OCI registry (env: MODEL_REGISTRY__*)
    model_registry: ModelRegistryConfig = Field(default_factory=ModelRegistryConfig)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

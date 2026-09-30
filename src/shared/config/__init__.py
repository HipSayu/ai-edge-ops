"""Reusable settings blocks, one per concern. Services compose the ones they need:

    class CloudSettings(ServiceSettings, PostgresSettings, RedisSettings, MqttSettings):
        model_config = SettingsConfigDict(env_prefix="CLOUD_", ...)

Blocks declare fields only; the concrete service sets `env_prefix`, so the same block
reads CLOUD_MQTT_HOST in cloud and EDGE_MQTT_HOST on the edge.
"""

from src.shared.config.api_key_settings import ApiKeySettings
from src.shared.config.cloud_api_settings import CloudApiSettings
from src.shared.config.llm_settings import LlmSettings
from src.shared.config.mqtt_settings import MqttSettings
from src.shared.config.postgres_settings import PostgresSettings
from src.shared.config.redis_settings import RedisSettings
from src.shared.config.service_settings import ServiceSettings

__all__ = [
    "ApiKeySettings",
    "CloudApiSettings",
    "LlmSettings",
    "MqttSettings",
    "PostgresSettings",
    "RedisSettings",
    "ServiceSettings",
]

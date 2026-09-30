from pathlib import Path
from typing import Literal

from pydantic_settings import SettingsConfigDict

from src.shared.config import ApiKeySettings, MqttSettings, PostgresSettings, RedisSettings, ServiceSettings


class CloudSettings(ServiceSettings, ApiKeySettings, PostgresSettings, RedisSettings, MqttSettings):
    model_config = SettingsConfigDict(env_prefix="CLOUD_", env_file=(".env", ".env.local"), extra="ignore")

    service_name: str = "cloud"

    # Auth. RSA private key (PEM file) signing access tokens with RS256, required (CLOUD_JWT_PRIVATE_KEY_FILE).
    # Its public key goes to the API gateway, which verifies tokens without being able to mint them.
    jwt_private_key_file: Path
    access_token_ttl_min: int = 30
    refresh_token_ttl_days: int = 7
    # The first account can always register (becomes ADMIN); later sign-ups need this flag
    allow_registration: bool = False

    # Model artifacts; None disables the model store
    model_store: Literal["huggingface"] | None = None
    hf_token: str | None = None
    hf_endpoint: str = "https://huggingface.co"
    hf_model_repo: str | None = None

    node_heartbeat_timeout_sec: float = 30.0
    # Run the MQTT consumers inside the API process (single-process deployments)
    embedded_worker: bool = False

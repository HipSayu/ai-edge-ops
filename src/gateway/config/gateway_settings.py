from pathlib import Path

from pydantic_settings import SettingsConfigDict

from src.shared.config import ServiceSettings


class GatewaySettings(ServiceSettings):
    model_config = SettingsConfigDict(env_prefix="GATEWAY_", env_file=(".env", ".env.local"), extra="ignore")

    service_name: str = "gateway"
    api_port: int = 8200

    # Public half of the Cloud's signing key (PEM file): verifies access tokens, cannot mint them
    jwt_public_key_file: Path
    jwt_issuer: str = "edgeops-cloud"

    # Upstreams: the assistant serves /api/v1/chat, the Cloud everything else
    cloud_url: str = "http://api:8000"
    assistant_url: str = "http://assistant:8100"
    connect_timeout_sec: float = 5.0

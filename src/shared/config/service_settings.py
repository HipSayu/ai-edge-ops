from pydantic_settings import BaseSettings


class ServiceSettings(BaseSettings):
    """Identity, HTTP bind address and logging every service has."""

    service_name: str = "service"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    log_json: bool = False

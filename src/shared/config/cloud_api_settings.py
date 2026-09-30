from pydantic_settings import BaseSettings


class CloudApiSettings(BaseSettings):
    """How a client service reaches the Cloud REST API."""

    cloud_api_url: str = "http://localhost:8000"
    cloud_api_key: str | None = None
    cloud_timeout_sec: float = 15.0

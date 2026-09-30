from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode


class ApiKeySettings(BaseSettings):
    """Keys accepted by this service's HTTP API; env value is comma-separated. Empty = auth disabled."""

    api_keys: Annotated[list[str], NoDecode] = []

    @field_validator("api_keys", mode="before")
    @classmethod
    def _split_keys(cls, value: object) -> object:
        if isinstance(value, str):
            return [k.strip() for k in value.split(",") if k.strip()]
        return value

from pydantic_settings import BaseSettings


class RedisSettings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"

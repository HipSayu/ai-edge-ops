from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLOUD_", env_file=".env", extra="ignore")

    # Everything persistent lives under data_dir (docker compose mounts the same folders)
    data_dir: Path = Path("volume/data")
    video_dir: Path = Path("volume/data/video")  # video/{cluster_id}/{node_id}/{camera_id}/
    database_url: str | None = None  # None: sqlite file inside data_dir

    # RS256 private key (PEM). Empty: a throwaway key is generated at startup (development only).
    jwt_private_key_path: Path | None = None
    jwt_ttl_min: int = 720

    grid_size: int = 9
    # MQTT broker the edge runtimes publish violations to. None: no subscription.
    mqtt_host: str | None = None
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_tls_ca: Path | None = None  # CA certificate (PEM) of the broker: set it to talk TLS (port 8883)

    # Shared state. None: everything stays in this process (development, tests).
    redis_url: str | None = None  # e.g. redis://:password@redis:6379/0
    event_seen_ttl_sec: int = 86400  # how long an edge event id is remembered to drop redeliveries

    # The detector app (services/detector), reachable only on the compose network. None: /detect is unavailable.
    detector_url: str | None = None  # e.g. http://detector:8400

    # What the assistant keeps: pictures attached to the chat, the reports it writes, the regulation documents it reads.
    image_dir: Path = Path("volume/data/chat_images")
    report_dir: Path = Path("volume/data/reports")
    regulation_dir: Path = Path("volume/regulations")  # *.md files, embedded into Qdrant and searched by meaning
    qdrant_url: str | None = None  # e.g. http://qdrant:6333. None: no regulation search
    qdrant_api_key: str | None = None
    qdrant_collection: str = "regulations"
    knowledge_min_score: float = 0.0  # cosine; passages scoring below are dropped (0: keep the top_k whatever they score)
    embedding_base_url: str | None = None  # any OpenAI-compatible /v1 (the `embedding` container in compose)
    embedding_model: str = "AITeamVN/Vietnamese_Embedding"
    embedding_api_key: str | None = None

    # The Dunly agent that answers the chat. None: /chat is unavailable. The API key needs the scopes sessions:read,
    # sessions:write and sessions:context (the user's token travels as context to the agent's connector).
    dunly_url: str | None = None  # e.g. http://dunly-api:8790
    dunly_api_key: str | None = None
    dunly_agent: str = "ppe-assistant"

    @property
    def snapshot_dir(self) -> Path:
        return self.data_dir / "snapshots"

    def resolved_database_url(self) -> str:
        return self.database_url or f"sqlite:///{(self.data_dir / 'cloud.db').as_posix()}"

"""What the use cases need from outside. Infrastructure implements these; nothing here imports it."""

from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO, Protocol

from cloud.application.dto.read_models import CameraRow, Overlay
from cloud.domain.violation.detection import DetectionResult
from cloud.domain.policy.regulation import Passage
from cloud.domain.model.user import User
from cloud.domain.model.zone import Zone


class PpeDetector(Protocol):
    """The detector service, which runs the PPE model (POST /detect with the picture's bytes)."""

    def detect(self, image: bytes) -> DetectionResult: ...


class CameraReader(Protocol):
    """Read side: every camera with the names of its node and cluster."""

    def rows(self) -> list[CameraRow]: ...


class FeedControl(Protocol):
    """The live camera feeds."""

    def ensure(self, camera_id: int, folder: Path) -> None: ...

    def drop(self, camera_id: int) -> None: ...

    def person_count(self, camera_id: int) -> int: ...

    def latest_frame(self, camera_id: int) -> bytes: ...

    def position(self, camera_id: int) -> float | None:
        """Where in its timeline the frame being shown is, in seconds. None when the camera has no feed."""

    def frame_after(self, camera_id: int, seq: int) -> tuple[int, float, float | None, bytes] | None:
        """The oldest kept frame newer than `seq`: (seq, seconds since it was made, position in the timeline or None, jpeg)."""


class DetectionLookup(Protocol):
    """The boxes the edges found."""

    def at(self, camera_id: int, position_sec: float) -> Overlay | None:
        """The boxes of the detection nearest to a position of the camera's timeline."""

    def around(self, camera_id: int, position_sec: float) -> tuple[Overlay | None, Overlay | None]:
        """The detections just before and just after a position."""

    def speed(self, camera_id: int) -> tuple[float, float, int] | None:
        """(detections per second, ms per detection, frames dropped) the edge reports for the camera."""

    def online(self, camera_id: int) -> bool:
        """Whether the edge has sent a detection for this camera recently; false if it never has or has gone quiet."""


class VideoStore(Protocol):
    """Video files on disk, one folder per camera."""

    def folder(self, cluster_id: int, node_id: int, camera_id: int) -> Path: ...

    def ensure_folder(self, cluster_id: int, node_id: int, camera_id: int) -> Path: ...

    def list_videos(self, cluster_id: int, node_id: int, camera_id: int) -> list[str]: ...

    def is_video_name(self, name: str) -> bool: ...

    def save(self, cluster_id: int, node_id: int, camera_id: int, filename: str, content: BinaryIO) -> None: ...

    def folders_on_disk(self) -> set[tuple[int, int, int]]: ...


class SnapshotStore(Protocol):
    """The frame saved with each violation."""

    def save(self, jpeg: bytes) -> str:
        """Returns the name to keep in the event."""

    def read(self, name: str) -> bytes | None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, stored: str) -> bool: ...


class TokenIssuer(Protocol):
    def issue(self, user: User) -> str: ...

    def public_pem(self) -> str: ...

    def jwks(self) -> dict: ...


class ZonePublisher(Protocol):
    """Tells the edge runtimes the zones of a camera."""

    def publish(self, camera_id: int, zones: list[Zone]) -> bool:
        """False when it could not be handed on (the broker is out of reach and the message could not even be queued)."""


class AgentChat(Protocol):
    """The agent that answers the chat (Dunly): one session per conversation, one turn per message."""

    @property
    def agent_name(self) -> str: ...

    def open_session(self, owner: int) -> str:
        """A new conversation of this user; returns its id."""

    def owns_session(self, session_id: str, owner: int) -> bool: ...

    def run_turn(self, session_id: str, items: list[dict], forward: dict[str, str]) -> Iterator[dict]:
        """Sends the input of a turn and yields the agent events as they arrive. `forward` (headers such as the user's
        Authorization) only travels with this call."""


class ImageStore(Protocol):
    """Pictures of the chat: what users attach and what the detector draws. Each belongs to one viewer."""

    def save(self, viewer_id: int, data: bytes, extension: str) -> str:
        """Returns the picture's id."""

    def read(self, viewer_id: int, image_id: str) -> tuple[bytes, str] | None:
        """(content, extension), or None when this viewer has no such picture."""


class ReportStore(Protocol):
    def save(self, title: str, body_markdown: str, author: str) -> str:
        """Returns the report id."""

    def read_docx(self, report_id: str) -> bytes | None: ...


class KnowledgeBase(Protocol):
    """The regulation documents the customer provided."""

    def search(self, query: str, top_k: int = 3) -> list[Passage]: ...

    def has_documents(self) -> bool: ...


class Embedder(Protocol):
    """Turns text into vectors for similarity search; one model, so every vector has the same size."""

    name: str  # identifies the model: documents embedded by another one are indexed again

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class VectorStore(Protocol):
    """Passages with their vectors, grouped by the file they came from. Vectors are compared by cosine."""

    def digests(self) -> dict[str, str]:
        """File name -> digest of the content it was indexed from."""

    def replace(self, source: str, digest: str, passages: list[Passage], vectors: list[list[float]]) -> bool:
        """Swaps everything held for `source`. True when the store had to drop all other files too (the vector size
        changed), so the caller must index them again."""

    def remove(self, source: str) -> None: ...

    def search(self, vector: list[float], top_k: int, min_score: float = 0.0) -> list[Passage]: ...

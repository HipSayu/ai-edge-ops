import uuid
from pathlib import Path


class FileSnapshotStore:
    """The SnapshotStore port: one jpg per violation, named by a random id."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def save(self, jpeg: bytes) -> str:
        self._folder.mkdir(parents=True, exist_ok=True)
        name = f"{uuid.uuid4().hex}.jpg"
        (self._folder / name).write_bytes(jpeg)
        return name

    def read(self, name: str) -> bytes | None:
        path = self._folder / Path(name).name  # a stored name never holds a directory part
        return path.read_bytes() if path.is_file() else None

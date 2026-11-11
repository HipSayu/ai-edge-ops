from pathlib import Path
import uuid

_EXTENSIONS = ("jpg", "png", "webp")


class FileImageStore:
    """The ImageStore port: one file per picture, in a folder per viewer."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def save(self, viewer_id: int, data: bytes, extension: str) -> str:
        image_id = uuid.uuid4().hex
        folder = self._folder / str(viewer_id)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{image_id}.{extension}").write_bytes(data)
        return image_id

    def read(self, viewer_id: int, image_id: str) -> tuple[bytes, str] | None:
        if not image_id.isalnum():  # ids are hex; anything else could be a path trick
            return None
        for extension in _EXTENSIONS:
            path = self._folder / str(viewer_id) / f"{image_id}.{extension}"
            if path.is_file():
                return path.read_bytes(), extension
        return None

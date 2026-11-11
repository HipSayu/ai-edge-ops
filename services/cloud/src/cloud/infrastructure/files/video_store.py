"""Video files on disk: volume/data/video/{cluster_id}/{node_id}/{camera_id}/*.mp4

The database is the source of truth. Folders are named by the ids, so a folder is only ever
attached to the one camera it belongs to.
"""

import shutil
from pathlib import Path
from typing import BinaryIO

VIDEO_SUFFIXES = {".mp4", ".avi", ".mkv"}


def camera_dir(root: Path, cluster_id: int, node_id: int, camera_id: int) -> Path:
    return root / str(cluster_id) / str(node_id) / str(camera_id)


def list_videos(folder: Path) -> list[str]:
    """File names in play order (sorted by name). Missing folder means no videos."""
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES)


def is_video_name(name: str) -> bool:
    return Path(name).suffix.lower() in VIDEO_SUFFIXES


def folders_on_disk(root: Path) -> set[tuple[int, int, int]]:
    """Every {cluster}/{node}/{camera} folder that exists under root, as id triples."""
    found: set[tuple[int, int, int]] = set()
    if not root.is_dir():
        return found
    for cluster in root.iterdir():
        if not cluster.is_dir() or not cluster.name.isdigit():
            continue
        for node in cluster.iterdir():
            if not node.is_dir() or not node.name.isdigit():
                continue
            for cam in node.iterdir():
                if cam.is_dir() and cam.name.isdigit():
                    found.add((int(cluster.name), int(node.name), int(cam.name)))
    return found


class FileVideoStore:
    """The VideoStore port on the local disk: video/{cluster_id}/{node_id}/{camera_id}/*.mp4"""

    def __init__(self, root: Path) -> None:
        self._root = root

    def folder(self, cluster_id: int, node_id: int, camera_id: int) -> Path:
        return camera_dir(self._root, cluster_id, node_id, camera_id)

    def ensure_folder(self, cluster_id: int, node_id: int, camera_id: int) -> Path:
        folder = self.folder(cluster_id, node_id, camera_id)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def list_videos(self, cluster_id: int, node_id: int, camera_id: int) -> list[str]:
        return list_videos(self.folder(cluster_id, node_id, camera_id))

    def is_video_name(self, name: str) -> bool:
        return is_video_name(name)

    def save(self, cluster_id: int, node_id: int, camera_id: int, filename: str, content: BinaryIO) -> None:
        folder = self.ensure_folder(cluster_id, node_id, camera_id)
        with (folder / Path(filename).name).open("wb") as out:  # Path.name drops any directory part
            shutil.copyfileobj(content, out)

    def folders_on_disk(self) -> set[tuple[int, int, int]]:
        return folders_on_disk(self._root)

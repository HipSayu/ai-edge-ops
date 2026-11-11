from pathlib import Path

from cloud.infrastructure.files.video_store import camera_dir, folders_on_disk, list_videos


def test_camera_folder_is_cluster_node_camera(tmp_path: Path):
    assert camera_dir(tmp_path, 2, 5, 9) == tmp_path / "2" / "5" / "9"


def test_list_videos_sorted_and_ignores_other_files(tmp_path: Path):
    folder = camera_dir(tmp_path, 1, 1, 1)
    folder.mkdir(parents=True)
    (folder / "b.mp4").write_bytes(b"x")
    (folder / "a.mp4").write_bytes(b"x")
    (folder / "notes.txt").write_bytes(b"x")
    assert list_videos(folder) == ["a.mp4", "b.mp4"]


def test_missing_folder_has_no_videos(tmp_path: Path):
    assert list_videos(tmp_path / "nope") == []


def test_folders_on_disk_only_reports_numeric_triples(tmp_path: Path):
    (tmp_path / "1" / "1" / "3").mkdir(parents=True)
    (tmp_path / "1" / "1" / "old").mkdir(parents=True)  # not an id, ignored
    (tmp_path / "junk.txt").write_text("x")
    assert folders_on_disk(tmp_path) == {(1, 1, 3)}

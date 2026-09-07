"""Video and camera frame helpers."""

from __future__ import annotations


def frames(source: str, *, loop: bool = False):
    """Yield frames from a camera, video file, or placeholder source."""
    try:
        import cv2  # noqa: PLC0415
    except ModuleNotFoundError:
        while True:
            yield None
        return
    video_source = int(source) if source.isdigit() else source
    while True:
        capture = cv2.VideoCapture(video_source)
        yielded = False
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                yielded = True
                yield frame
        finally:
            capture.release()
        if not loop or not yielded:
            return


__all__ = ["frames"]
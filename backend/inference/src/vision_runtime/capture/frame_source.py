"""Camera / video-file frame generator (blocking — call from a thread)."""

from __future__ import annotations

# Yielded when OpenCV isn't installed: keeps the pipeline ticking (the dummy
# runtime ignores frame content) without pulling in cv2 for CI / dev.
NO_CV2_FRAME = object()


def frames(source: str, *, loop: bool = False):
    """Yield frames from a camera, video file, or (no cv2) a placeholder."""
    try:
        import cv2  # noqa: PLC0415
    except ModuleNotFoundError:
        while True:
            yield NO_CV2_FRAME

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


__all__ = ["NO_CV2_FRAME", "frames"]
